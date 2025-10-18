from __future__ import annotations

"""
Асинхронные утилиты:
- fire_and_forget() / run_coro_threadsafe()
- a_timeout(), a_retry()
- Debouncer, Throttler
- gather_limited()
- to_thread(), run_sync()
"""

import asyncio
import contextlib
import time
from typing import Any, Awaitable, Callable, Iterable, Sequence, TypeVar

try:
    # предпочитаем наш structlog-логер
    from ..core.logging import logger  # type: ignore
except Exception:  # fallback на stdlib
    import logging

    logger = logging.getLogger("asyncio-tools")

T = TypeVar("T")


def get_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def fire_and_forget(coro: Awaitable[Any], *, name: str | None = None) -> asyncio.Task[Any]:
    """
    Запускает корутину без ожидания (фон). Исключения логируются.
    """
    loop = get_loop()
    task = loop.create_task(coro, name=name)

    def _done(t: asyncio.Task[Any]) -> None:
        with contextlib.suppress(asyncio.CancelledError):
            exc = t.exception()
            if exc:
                logger.warning("bg_task_failed", name=getattr(t, "get_name", lambda: None)(), error=repr(exc))

    task.add_done_callback(_done)
    return task


def run_coro_threadsafe(coro: Awaitable[T]) -> T:
    """
    Выполнить корутину из синхронного кода (например, обработчик кнопки в Flet).
    Если цикл уже запущен в текущем потоке — блокирующе исполняет через run_until_complete.
    """
    try:
        loop = asyncio.get_running_loop()
        # если уже в async-контексте — это ошибка, корутина должна быть awaited
        raise RuntimeError("run_coro_threadsafe() called from running loop; use `await`")
    except RuntimeError:
        # нет активного цикла — запускаем новый
        return asyncio.run(coro)


async def a_timeout(coro: Awaitable[T], timeout: float) -> T:
    return await asyncio.wait_for(coro, timeout=timeout)


async def a_retry(
    func: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """
    Повтор выполнения корутины с экспоненциальной задержкой.
    """
    attempt = 0
    cur_delay = delay
    while True:
        try:
            return await func()
        except retry_on as e:  # type: ignore[misc]
            attempt += 1
            if attempt > retries:
                raise
            logger.warning("retry", attempt=attempt, error=repr(e))
            await asyncio.sleep(cur_delay)
            cur_delay *= backoff


class Debouncer:
    """
    Отложенный вызов корутины: пока приходят новые вызовы — старые отменяются.
    Полезно для поиска/валидации "на лету".
    """

    def __init__(self, delay: float = 0.3) -> None:
        self.delay = delay
        self._task: asyncio.Task[Any] | None = None

    async def call(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        async def _runner():
            await asyncio.sleep(self.delay)
            await func(*args, **kwargs)

        self._task = asyncio.create_task(_runner())

    def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()


class Throttler:
    """
    Ограничивает частоту вызовов (не чаще, чем раз в min_interval секунд).
    """

    def __init__(self, min_interval: float = 0.3) -> None:
        self.min_interval = min_interval
        self._last: float = 0.0
        self._lock = asyncio.Lock()

    async def __call__(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self._last = time.monotonic()
        return await func(*args, **kwargs)


async def gather_limited(limit: int, coros: Iterable[Awaitable[T]]) -> Sequence[T]:
    """
    Параллельное выполнение, но не более `limit` задач одновременно.
    """
    sem = asyncio.Semaphore(max(1, limit))

    async def _wrap(c: Awaitable[T]) -> T:
        async with sem:
            return await c

    tasks = [asyncio.create_task(_wrap(c)) for c in coros]
    return await asyncio.gather(*tasks)


async def to_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    return await asyncio.to_thread(func, *args, **kwargs)


def run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Запустить синхронную функцию в отдельном потоке из async-кода.
    """
    return get_loop().run_until_complete(to_thread(func, *args, **kwargs))
