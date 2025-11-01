from __future__ import annotations
"""
Асинхронные утилиты:
- get_loop()
- fire_and_forget()          — запустить корутину в фоне (если нет цикла — отдельный поток)
- run_coro_threadsafe()      — выполнить корутину из синхронного кода (без активного цикла)
- a_timeout()                — таймаут на любую корутину
- a_retry()                  — ретраи с бэкоффом и джиттером
- Debouncer                  — «отложенный» вызов (сбрасывается при новых инпутах)
- Throttler                  — вызовы не чаще min_interval
- gather_limited()           — параллелизм с ограничением
- to_thread() / run_sync()   — запуск sync-функции в thread-пуле (есть async- и sync-варианты)
"""

from typing import Any, Awaitable, Callable, Iterable, Sequence, TypeVar, Optional
import asyncio
import contextlib
import random
import time
import threading

try:
    # предпочитаем наш structlog-логер
    from ..core.logging import logger  # type: ignore
except Exception:  # fallback на stdlib
    import logging
    logger = logging.getLogger("asyncio-tools")

T = TypeVar("T")


# --------------------------------------------------------------------------- #
# Loop helpers
# --------------------------------------------------------------------------- #

def get_loop() -> asyncio.AbstractEventLoop:
    """
    Возвращает текущий «запущенный» цикл, иначе создаёт НОВЫЙ и делает его текущим.
    ВНИМАНИЕ: создание нового цикла не запускает его автоматически.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# --------------------------------------------------------------------------- #
# Fire & forget / thread-safe run
# --------------------------------------------------------------------------- #

def fire_and_forget(coro: Awaitable[Any], *, name: str | None = None) -> Optional[asyncio.Task[Any]]:
    """
    Запускает корутину «в фоне».
    - Если есть активный цикл в текущем потоке → create_task().
    - Если цикла нет → запустим отдельный DAEMON-поток с собственным loop и asyncio.run().
      В этом режиме возвращается None (нет asyncio.Task в текущем loop).

    Возврат:
      asyncio.Task | None
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Нет активного цикла — отдадим выполнение отдельному потоку
        def _runner():
            try:
                asyncio.run(coro)
            except Exception as exc:  # noqa: BLE001
                logger.warning("bg_thread_task_failed", error=repr(exc))
        th = threading.Thread(target=_runner, name=name or "fire-and-forget", daemon=True)
        th.start()
        return None

    task = loop.create_task(coro, name=name)

    def _done(t: asyncio.Task[Any]) -> None:
        with contextlib.suppress(asyncio.CancelledError):
            exc = t.exception()
            if exc:
                try:
                    name_ = t.get_name() if hasattr(t, "get_name") else name
                except Exception:
                    name_ = name
                logger.warning("bg_task_failed", name=name_, error=repr(exc))

    task.add_done_callback(_done)
    return task


def run_coro_threadsafe(coro: Awaitable[T]) -> T:
    """
    Выполнить корутину из СИНХРОННОГО контекста (где нет активного loop) блокирующе.
    Если цикл уже запущен в текущем потоке — кидаем исключение (используйте `await`).

    Пример:
        result = run_coro_threadsafe(do_work_async())
    """
    try:
        asyncio.get_running_loop()
        # Мы уже в async-контексте → это ошибка использования API.
        raise RuntimeError("run_coro_threadsafe() called from a running loop; use `await` instead")
    except RuntimeError:
        # Нет активного цикла в текущем потоке → можно безопасно выполнить
        return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# Timeout / Retry
# --------------------------------------------------------------------------- #

async def a_timeout(coro: Awaitable[T], timeout: float) -> T:
    return await asyncio.wait_for(coro, timeout=timeout)


async def a_retry(
    func: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    jitter: float = 0.1,
    retry_on: tuple[type[BaseException], ...] = (Exception, ),
    on_retry: Optional[Callable[[int, BaseException], None]] = None,
) -> T:
    """
    Повтор выполнения корутины с экспоненциальной задержкой и джиттером.

    Параметры:
      retries  — количество повторов (без первой попытки)
      delay    — стартовая задержка, сек
      backoff  — множитель бэкоффа (>=1.0)
      jitter   — добавочный ±%, например 0.1 → ±10%
      retry_on — кортеж исключений для повторов
      on_retry — callback(attempt, exc) перед сном
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
            # джиттер
            j = 1.0 + random.uniform(-jitter, jitter) if jitter > 0 else 1.0
            sleep_for = max(0.0, cur_delay * j)
            logger.warning("retry", attempt=attempt, delay=sleep_for, error=repr(e))
            if on_retry:
                with contextlib.suppress(Exception):
                    on_retry(attempt, e)
            await asyncio.sleep(sleep_for)
            cur_delay *= max(1.0, backoff)


# --------------------------------------------------------------------------- #
# Debounce / Throttle
# --------------------------------------------------------------------------- #

class Debouncer:
    """
    Отложенный вызов корутины: пока приходят новые вызовы — предыдущая задача отменяется.
    Полезно для поиска/валидации «на лету».
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


# --------------------------------------------------------------------------- #
# Concurrency helpers
# --------------------------------------------------------------------------- #

async def gather_limited(limit: int, coros: Iterable[Awaitable[T]]) -> Sequence[T]:
    """
    Параллельное выполнение, но не более `limit` задач одновременно.
    Сохраняет порядок результатов как в исходной коллекции.
    """
    sem = asyncio.Semaphore(max(1, limit))

    async def _wrap(c: Awaitable[T]) -> T:
        async with sem:
            return await c

    tasks = [asyncio.create_task(_wrap(c)) for c in coros]
    return await asyncio.gather(*tasks)


# --------------------------------------------------------------------------- #
# Sync ↔ Async bridges
# --------------------------------------------------------------------------- #

async def to_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Асинхронно выполнить синхронную функцию в пуле потоков."""
    return await asyncio.to_thread(func, *args, **kwargs)


async def run_sync_async(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Вызов синхронной функции из async-кода.
    Эквивалентен: `await to_thread(func, *args, **kwargs)`.
    """
    return await to_thread(func, *args, **kwargs)


def run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Вызов синхронной функции из СИНХРОННОГО кода, но в отдельном потоке.
    Полезно, когда хочется из обычной функции «не блокировать» GUI/цикл событий.

    Пример:
        result = run_sync(io_bound_func, path)
    """
    return asyncio.run(to_thread(func, *args, **kwargs))
