from typing import Collection, Iterable, Sequence, SupportsIndex, overload

from pytableaux.tools import abcs
from pytableaux.typing import _VT, _MSeqT, _SeqT


class SeqCover(Sequence[_VT], abcs.Copyable): ...
