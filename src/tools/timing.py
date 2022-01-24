from __future__ import annotations

import errors as err
import tools.misc as misc
from time import time as _time

def _nowms() -> int:
    'Current time in milliseconds'
    return int(round(_time() * 1000))

class StopWatch:
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
            raise err.IllegalStateError('StopWatch already started.')
        self.count += 1
        self._running = True
        self._start_time = _nowms()

    def stop(self):
        'Stop the StopWatch. Raises IllegalStateError if already stopped.'
        if not self._running:
            raise err.IllegalStateError('StopWatch already stopped.')
        self._running = False
        self._accum += _nowms() - self._start_time

    def reset(self):
        'Reset elapsed to 0.'
        self._accum = 0
        if self._running:
            self._start_time = _nowms()

    @property
    def elapsed(self) -> int:
        'Elapsed milliseconds.'
        if self._running:
            return self._accum + (_nowms() - self._start_time)
        return self._accum

    @property
    def elapsed_avg(self) -> float:
        'Elapsed milliseconds / count.'
        try:
            return self.elapsed / self.count
        except ZeroDivisionError:
            return 0

    @property
    def running(self) -> bool:
        'Whether the StopWatch is running.'
        return self._running

    def __repr__(self):
        return misc.wraprepr(self, self.elapsed)

    def __float__(self):
        return float(self.elapsed)

    def __int__(self):
        return self.elapsed

    def __str__(self):
        return str(self.elapsed)

    def __enter__(self) -> StopWatch:
        'Start/stop context entry.'
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self._running:
            self.stop()

    # @staticmethod
    # def _nowms() -> int:
    #     'Current time in milliseconds'
    #     return int(round(_time() * 1000))