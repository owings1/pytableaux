from __future__ import annotations as _

__all__ = 'StopWatch', 'Counter'

from errors import IllegalStateError

from time import time as _time
from typing import Iterator, TypeVar

def _nowms() -> int:
    'Current time in milliseconds'
    return int(round(_time() * 1000))

class TimingCommon:
    @classmethod
    def gen(cls: type[TimT], n: int, *args, **kw) -> Iterator[TimT]:
        return (cls(*args, **kw) for _ in range(n))

TimT = TypeVar('TimT', bound = TimingCommon)

class StopWatch(TimingCommon):
    'Millisecond stopwatch.'

    __slots__ = '_start_time', '_accum', '_running', 'count'

    def __init__(self, started = False):
        self._start_time = None
        self._accum = 0
        self.count = 0
        self._running = False
        if started:
            self.start()

    def start(self):
        'Start the StopWatch. Raises IllegalStateError if already started.'
        if self._running:
            raise IllegalStateError('StopWatch already started.')
        self.count += 1
        self._running = True
        self._start_time = _nowms()

    def stop(self):
        'Stop the StopWatch. Raises IllegalStateError if already stopped.'
        if not self._running:
            raise IllegalStateError('StopWatch already stopped.')
        self._running = False
        self._accum += _nowms() - self._start_time

    def reset(self):
        'Reset elapsed to 0.'
        self._accum = 0
        if self._running:
            self._start_time = _nowms()
        else:
            self._start_time = None
        return self

    def clear(self):
        self.reset()
        self.count = 0
        return self

    def elapsed(self) -> int:
        'Elapsed milliseconds.'
        return self.elapsed_ms()

    def elapsed_avg(self) -> float:
        'Elapsed milliseconds / count.'
        try:
            return self.elapsed() / self.count
        except ZeroDivisionError:
            return 0

    def elapsed_secs(self):
        return self.elapsed() // 1000

    def elapsed_ms(self):
        'Elapsed milliseconds.'
        if self._running:
            return self._accum + (_nowms() - self._start_time)
        return self._accum

    @property
    def running(self) -> bool:
        'Whether the StopWatch is running.'
        return self._running

    def summary(self):
        return dict(
            elapsed_ms  = self.elapsed_ms(),
            count       = self.count,
            elapsed_avg = self.elapsed_avg(),
        )

    def __repr__(self):
        from tools.misc import wraprepr
        return wraprepr(self, self.elapsed())

    def __float__(self):
        return float(self.elapsed())

    def __int__(self):
        return self.elapsed()

    def __str__(self):
        return str(self.elapsed())

    def __enter__(self) -> StopWatch:
        'Start/stop context entry.'
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self._running:
            self.stop()

class Counter(TimingCommon):
    __slots__ = 'value',
    def __init__(self, value = 0):
        self.value = value
    def inc(self, n = 1):
        self.value += n
    def __int__(self):
        return self.value
    def __repr__(self):
        return '<%s:%s>' % (type(self).__name__, self.value)