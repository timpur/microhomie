import sys
from micropython import const
import uasyncio.core as asyncio

POLL_MS = const(10)


async def runner(coro):
    try:
        await coro
    except asyncio.CancelledError:
        raise
    except Exception as error:
        sys.print_exception(error)


class WaitForMS:
    def __init__(self, timeout=None):
        self._timeout = timeout
        self._cancelled = False
        self._coro = None
        self._cancel_coro = None
        self._event_loop = asyncio.get_event_loop()

    async def __aenter__(self):
        return self.do_enter()

    async def __aexit__(self, *args):
        self.do_exit()

    def do_enter(self):
        if self._timeout is None:
            return self

        self._coro = asyncio.get_event_loop().cur_task
        if self._coro is None:
            raise RuntimeError('WaitForMS context manager can only be used inside a task')

        self._cancel_coro = self._cancel()
        self._event_loop.call_later_ms(self._timeout, self._cancel_coro)
        return self

    def do_exit(self):
        self._coro = None
        self._cancel_coro = None

    async def _cancel(self):
        if self._coro:
            asyncio.cancel(self._coro)
            self._cancelled = True


class WaitForStateToBe:
    def __init__(self, store, path, value, only_change=False, ms=POLL_MS):
        self._store = store
        self._path = path
        self._value = value
        self._ms = ms
        self._flag = False
        self._sub = store.subscribe(self._check)
        if not only_change:
            self._check(path, store.get(path))

    def _check(self, key, new_value, *args):
        if not key == self._path:
            return
        if new_value == self._value:
            self._flag = True

    async def __await__(self):
        while True:
            await asyncio.sleep_ms(self._ms)
            if self._flag:
                self._store.unsubscribe(self._sub)
                return self._store.get(self._path)

    __iter__ = __await__
