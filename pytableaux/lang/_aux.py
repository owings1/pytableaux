from __future__ import annotations

__all__ = ()

import reprlib
from typing import NamedTuple

class BiCoords(NamedTuple):
    index     : int
    subscript : int

    class Sorting(NamedTuple):
        subscript : int
        index     : int

    def sorting(self) -> BiCoords.Sorting:
        return self.Sorting(self.subscript, self.index)

    first = (0, 0)

    def __repr__(self):
        return repr(tuple(self))

class TriCoords(NamedTuple):
    index     : int
    subscript : int
    arity     : int

    class Sorting(NamedTuple):
        subscript : int
        index     : int
        arity     : int

    def sorting(self) -> TriCoords.Sorting:
        return self.Sorting(self.subscript, self.index, self.arity)

    first = (0, 0, 1)

    def __repr__(self):
        return repr(tuple(self))

BiCoords.first = BiCoords._make(BiCoords.first)
TriCoords.first = TriCoords._make(TriCoords.first)



