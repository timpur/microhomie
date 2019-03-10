import _thread
import utime as time
import uasyncio.core as asyncio

STARTED = 'started'
RUNNING = 'running'
STOPPED = 'stopped'


class Thread:
    _id = 0

    def __init__(self):
        Thread._id += 1
        self._id = Thread._id
        self._state = STOPPED
        self._lock = _thread.allocate_lock()

    def start(self, fn, *args):
        if self._state != STOPPED:
            raise Exception('thread already running')
        with self._lock:
            self._state = STARTED
        print('t:', _thread.start_new_thread(self._run, (fn, self)+args))

    def _run(self, fn, *args):
        with self._lock:
            self._state = RUNNING
        result = fn(*args)
        with self._lock:
            self._state = STOPPED
        return result


class LoopThread(Thread):
    def __init__(self):
        super().__init__()
        self._exit = False

    def stop(self):
        with self._lock:
            self._exit = True

    def _run(self, fn, *args):
        with self._lock:
            self._state = RUNNING
        while True:
            if self._exit:
                break
            fn(*args)
        with self._lock:
            self._exit = False
            self._state = STOPPED


class TaskThread(Thread):
    def __init__(self):
        super().__init__()
        self._result = None

    def start(self, fn, *args, blocking=True):
        super().start(fn, *args)
        if blocking:
            while self._state != STOPPED:
                time.sleep(10)
            return self._result

    def _run(self, fn, *args):
        result = super()._run(fn, *args)
        with self._lock:
            self._result = result

    async def __await__(self):
        while True:
            if self._state == STOPPED:
                return self._result
            await asyncio.sleep_ms(10)

    __iter__ = __await__
