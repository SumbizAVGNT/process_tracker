"""
Утилиты для asyncio (без внешних зависимостей).

Возможности:
- retry(...)                 — повтор с экспон. бэкоффом и джиттером
- wait_for(coro, timeout)    — безопасный таймаут-обёртка
- gather_limited(...)        — параллельное выполнение с ограничением concurrency
- fire_and_forget(coro, ...) — создать таск с безопасным логированием исключений
- BackgroundTasks            — менеджер фоновых задач (контекстный)
- Debouncer                  — "последний вызов побеждает" (анти-дребезг)
- Throttler                  — минимальный интервал между вызовами (троттлинг)
"""

from __future__ import annotations

import asyncio
import logging
import random
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
    """
    Выполнить корутину с таймаутом (если timeout=None — без таймаута).
    Корректно отменяет только текущий await, не отменяя внешние таски.
    """
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
    """
    Повтор выполнения корутины с экспоненциальным бэкоффом и джиттером.
    - retries: сколько ПОВТОРОВ сделать при ошибке (итого попыток = retries+1)
    - exceptions: перехватываемые исключения
    - delay/backoff/max_delay: параметры бэкоффа
    - jitter: 0..1 — доля случайного разброса задержки
    - timeout: таймаут на каждую попытку
    """
    attempt = 0
    current_delay = max(0.0, delay)

    while True:
        try:
            return await wait_for(coro_factory(), timeout)
        except exceptions as exc:  # noqa: B902
            if attempt >= retries:
                raise
            sleep_for = min(current_delay, max_delay)
            # добавляем +-jitter*delay
            if jitter:
                delta = sleep_for * jitter
                sleep_for = max(0.0, sleep_for + random.uniform(-delta, delta))
            if on_retry:
                try:
                    on_retry(attempt + 1, exc, sleep_for)
                except Exception:  # защитим on_retry
                    logger.exception("on_retry callback raised")
            await asyncio.sleep(sleep_for)
            attempt += 1
            current_delay *= backoff


def fire_and_forget(coro: Awaitable[Any], *, name: Optional[str] = None) -> asyncio.Task:
    """
    Создать фоновую задачу и залогировать исключение, если оно произойдёт.
    """
    task = asyncio.create_task(coro, name=name)

    def _done(t: asyncio.Task) -> None:
        try:
            _ = t.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Background task error (name=%s)", getattr(t, "get_name", lambda: name)())

    task.add_done_callback(_done)
    return task


# ----------------------------- Ограничение concurrency ----------------------------- #

async def gather_limited(
    concurrency: int,
    coroutines_or_factories: Iterable[Union[Awaitable[T], Callable[[], Awaitable[T]]]],
    *,
    return_exceptions: bool = False,
) -> list[T]:
    """
    Запустить задачи с ограничением параллелизма (concurrency).
    Поддерживает как готовые корутины, так и фабрики без аргументов.

    Результаты возвращаются в исходном порядке.
    """
    semaphore = asyncio.Semaphore(max(1, concurrency))
    results: list[Optional[T]] = [None] * len(list(coroutines_or_factories))  # type: ignore
    # перечитаем итератор в список с сохранением порядка
    items: list[Union[Awaitable[T], Callable[[], Awaitable[T]]]] = list(coroutines_or_factories)

    async def _run_one(idx: int):
        async with semaphore:
            try:
                obj = items[idx]
                if callable(obj):
                    res = await obj()  # type: ignore[func-returns-value]
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
        # В случае исключения — аккуратно отменим остальные
        for t in tasks:
            if not t.done():
                t.cancel()
        raise
    return results  # type: ignore[return-value]


# ----------------------------- Менеджер фоновых задач ----------------------------- #

class BackgroundTasks:
    """
    Контекстный менеджер для управления набором фоновых задач.

    Пример:
        async with BackgroundTasks() as bg:
            bg.create(worker())
            ...
        # при выходе все незавершённые задачи отменятся и дождутся
    """

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    def create(self, coro: Awaitable[Any], *, name: Optional[str] = None) -> asyncio.Task:
        t = fire_and_forget(coro, name=name)
        self._tasks.add(t)
        t.add_done_callback(lambda _t: self._tasks.discard(_t))
        return t

    async def cancel_all(self) -> None:
        if not self._tasks:
            return
        for t in list(self._tasks):
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def __aenter__(self) -> "BackgroundTasks":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.cancel_all()


# ----------------------------- Debounce / Throttle ----------------------------- #

class Debouncer:
    """
    Анти-дребезг: выполняет только ПОСЛЕДНИЙ вызов через задержку wait.
    Если приходят новые вызовы — предыдущий таймер отменяется.
    Поддерживает только async-функции (корутины).
    """

    def __init__(self, wait: float = 0.3) -> None:
        self.wait = max(0.0, wait)
        self._timer: Optional[asyncio.Task] = None
        self._pending_coro_factory: Optional[Callable[[], Awaitable[Any]]] = None

    def call(self, coro_factory: Callable[[], Awaitable[Any]]) -> None:
        """Запланировать выполнение."""
        self._pending_coro_factory = coro_factory
        # сбрасываем предыдущий таймер
        if self._timer and not self._timer.done():
            self._timer.cancel()
        self._timer = asyncio.create_task(self._run())

    async def flush(self) -> None:
        """Выполнить немедленно, если есть запланированное."""
        if self._timer and not self._timer.done():
            self._timer.cancel()
        await self._execute_pending()

    def cancel(self) -> None:
        """Отменить запланированный вызов."""
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
    """
    Троттлер: обеспечивает минимальный интервал между вызовами (min_interval сек).
    Вызов `await throttler.wait()` перед действием гарантирует задержку при необходимости.
    """
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
    """
    Лёгкая очередь последних событий фиксированного размера (in-memory).
    Можно использовать как кольцевой буфер + asyncio.Queue для слушателей.
    """
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
