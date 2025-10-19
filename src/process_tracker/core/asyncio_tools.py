from __future__ import annotations

import asyncio
import logging
import random
import threading
from collections import deque
from dataclasses import dataclass
from time import monotonic
from typing import (
    Any,
    Awaitable,
    Callable,
    Deque,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


# ----------------------------- Базовые обёртки ----------------------------- #

async def wait_for(coro: Awaitable[T], timeout: Optional[float]) -> T:
    if timeout is None or timeout <= 0:
        return await coro
    return await asyncio.wait_for(coro, timeout=timeout)


async def retry(
    coro_factory: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    exceptions: Tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.25,
    backoff: float = 2.0,
    max_delay: float = 5.0,
    jitter: float = 0.10,
    timeout: Optional[float] = None,
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
) -> T:
    attempt = 0
    current_delay = max(0.0, delay)

    while True:
        try:
            return await wait_for(coro_factory(), timeout)
        except exceptions as exc:  # noqa: B902
            if attempt >= retries:
                raise
            sleep_for = min(current_delay, max_delay)
            if jitter:
                delta = sleep_for * jitter
                sleep_for = max(0.0, sleep_for + random.uniform(-delta, delta))
            if on_retry:
                try:
                    on_retry(attempt + 1, exc, sleep_for)
                except Exception:
                    logger.exception("on_retry callback raised")
            await asyncio.sleep(sleep_for)
            attempt += 1
            current_delay *= backoff


def fire_and_forget(coro: Awaitable[Any], *, name: Optional[str] = None):
    """
    Запустить корутину "в фоне" надёжно и залогировать способ запуска.
    Может вернуть asyncio.Task (если текущий loop) или None.
    """
    # 1) Есть running loop в текущем потоке
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        logger.debug("fire_and_forget: using running loop (task) name=%s", name or "n/a")
        task = loop.create_task(coro, name=name)

        def _done(t: asyncio.Task) -> None:
            try:
                _ = t.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Background task error (name=%s)", getattr(t, "get_name", lambda: name)())
        task.add_done_callback(_done)
        return task

    # 2) Есть loop, но он запущен в другом потоке
    try:
        other_loop = asyncio.get_event_loop()
    except RuntimeError:
        other_loop = None

    if other_loop and other_loop.is_running():
        logger.debug("fire_and_forget: using run_coroutine_threadsafe name=%s", name or "n/a")
        fut = asyncio.run_coroutine_threadsafe(coro, other_loop)

        def _done(_f):
            try:
                _f.result()
            except Exception:
                logger.exception("Background task error (threadsafe, name=%s)", name or "fire-and-forget")
        fut.add_done_callback(_done)
        return None

    # 3) Нет ни одного запущенного loop — запускаем отдельный поток с asyncio.run()
    logger.debug("fire_and_forget: spawning background thread name=%s", name or "n/a")

    def _runner():
        try:
            asyncio.run(coro)
        except Exception:
            logger.exception("Background thread task error (name=%s)", name or "fire-and-forget")

    t = threading.Thread(target=_runner, name=name or "fire-and-forget", daemon=True)
    t.start()
    return None


# ----------------------------- Ограничение concurrency ----------------------------- #

async def gather_limited(
    concurrency: int,
    coroutines_or_factories: Iterable[Union[Awaitable[T], Callable[[], Awaitable[T]]]],
    *,
    return_exceptions: bool = False,
) -> list[T]:
    semaphore = asyncio.Semaphore(max(1, concurrency))
    items: list[Union[Awaitable[T], Callable[[], Awaitable[T]]]] = list(coroutines_or_factories)
    results: list[Optional[T]] = [None] * len(items)  # type: ignore

    async def _run_one(idx: int):
        async with semaphore:
            try:
                obj = items[idx]
                if callable(obj):
                    res = await obj()  # type: ignore
                else:
                    res = await obj  # type: ignore[misc]
                results[idx] = res
            except Exception as e:
                if return_exceptions:
                    results[idx] = e  # type: ignore[assignment]
                else:
                    raise

    tasks = [asyncio.create_task(_run_one(i)) for i in range(len(items))]
    try:
        await asyncio.gather(*tasks)
    except Exception:
        for t in tasks:
            if not t.done():
                t.cancel()
        raise
    return results  # type: ignore[return-value]


# ----------------------------- Менеджер фоновых задач ----------------------------- #

class BackgroundTasks:
    def __init__(self) -> None:
        self._tasks: set[Any] = set()

    def create(self, coro: Awaitable[Any], *, name: Optional[str] = None):
        t = fire_and_forget(coro, name=name)
        self._tasks.add(t)
        return t

    async def cancel_all(self) -> None:
        for t in list(self._tasks):
            if isinstance(t, asyncio.Task) and not t.done():
                t.cancel()
        if any(isinstance(t, asyncio.Task) for t in self._tasks):
            await asyncio.gather(
                *(t for t in self._tasks if isinstance(t, asyncio.Task)),
                return_exceptions=True,
            )
        self._tasks.clear()

    async def __aenter__(self) -> "BackgroundTasks":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.cancel_all()


# ----------------------------- Debounce / Throttle ----------------------------- #

class Debouncer:
    def __init__(self, wait: float = 0.3) -> None:
        self.wait = max(0.0, wait)
        self._timer: Optional[asyncio.Task] = None
        self._pending_coro_factory: Optional[Callable[[], Awaitable[Any]]] = None

    def call(self, coro_factory: Callable[[], Awaitable[Any]]) -> None:
        self._pending_coro_factory = coro_factory
        if self._timer and not self._timer.done():
            self._timer.cancel()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            self._timer = loop.create_task(self._run())

    async def flush(self) -> None:
        if self._timer and not self._timer.done():
            self._timer.cancel()
        await self._execute_pending()

    def cancel(self) -> None:
        if self._timer and not self._timer.done():
            self._timer.cancel()
        self._pending_coro_factory = None

    async def _run(self) -> None:
        try:
            await asyncio.sleep(self.wait)
            await self._execute_pending()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Debouncer run error")

    async def _execute_pending(self) -> None:
        factory = self._pending_coro_factory
        self._pending_coro_factory = None
        if factory is None:
            return
        try:
            await factory()
        except Exception:
            logger.exception("Debouncer callback error")


@dataclass
class Throttler:
    min_interval: float = 0.3
    _last: float = 0.0

    async def wait(self) -> None:
        now = monotonic()
        delay = (self._last + self.min_interval) - now
        if delay > 0:
            await asyncio.sleep(delay)
        self._last = monotonic()


# ----------------------------- Простейшая очередь событий ----------------------------- #

class AsyncEventQueue:
    def __init__(self, history: int = 100) -> None:
        self._history: Deque[Any] = deque(maxlen=max(1, history))
        self._queue: "asyncio.Queue[Any]" = asyncio.Queue()

    def put_nowait(self, event: Any) -> None:
        self._history.append(event)
        self._queue.put_nowait(event)

    def get_nowait(self) -> Any:
        return self._queue.get_nowait()

    async def get(self) -> Any:
        return await self._queue.get()

    def last(self) -> Sequence[Any]:
        return tuple(self._history)
