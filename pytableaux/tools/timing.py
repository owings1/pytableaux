# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.tools.timing
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from time import time as _time

from pytableaux.errors import IllegalStateError

__all__ = 'StopWatch', 'Counter'

def _nowms() -> int:
    'Current time in milliseconds'
    return int(round(_time() * 1000))

class TimingCommon:

    @classmethod
    def gen(cls, n: int, *args, **kw):
        return (cls(*args, **kw) for _ in range(n))


class StopWatch(TimingCommon):
    'Millisecond stopwatch.'

    __slots__ = '_start_time', '_accum', '_running', 'count'

    count: int

    def __init__(self, started = False):
        self._start_time = None
        self._accum = 0
        self.count = 0
        self._running = False
        if started:
            self.start()

    @property
    def running(self) -> bool:
        'Whether the StopWatch is running.'
        return self._running

    def start(self) -> None:
        'Start the StopWatch. Raises IllegalStateError if already started.'
        if self._running:
            raise IllegalStateError('StopWatch already started.')
        self.count += 1
        self._running = True
        self._start_time = _nowms()

    def stop(self) -> None:
        'Stop the StopWatch. Raises IllegalStateError if already stopped.'
        if not self._running:
            raise IllegalStateError('StopWatch already stopped.')
        self._running = False
        self._accum += _nowms() - self._start_time

    def reset(self) -> StopWatch:
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

    def elapsed(self):
        'Elapsed milliseconds.'
        return self.elapsed_ms()

    def elapsed_avg(self):
        'Elapsed milliseconds / count.'
        try:
            return self.elapsed() / self.count
        except ZeroDivisionError:
            return 0.0

    def elapsed_secs(self):
        'Elapsed seconds.'
        return self.elapsed() // 1000

    def elapsed_ms(self):
        'Elapsed milliseconds.'
        if self._running:
            return self._accum + (_nowms() - self._start_time)
        return self._accum

    def summary(self):
        return dict(
            elapsed_ms  = self.elapsed_ms(),
            count       = self.count,
            elapsed_avg = self.elapsed_avg())

    def _asdict(self):
        'JSON Comptibility'
        return self.summary()

    for_json = _asdict

    def __repr__(self):
        return f'{type(self).__name__}({self.elapsed_ms()})'

    def __float__(self):
        return float(self.elapsed())

    def __int__(self):
        return self.elapsed()

    def __str__(self):
        return str(self.elapsed())

    def __enter__(self):
        'Start/stop context entry.'
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self._running:
            self.stop()

class Counter(TimingCommon):

    __slots__ = 'value',

    value: int

    __hash__ = None

    def __init__(self, value = 0):
        self.value = value

    def inc(self, n = 1):
        self.value += n

    def __index__(self):
        return self.value

    for_json = __index__
    __int__ = __index__

    def __repr__(self):
        return '<%s:%s>' % (type(self).__name__, self.value)


