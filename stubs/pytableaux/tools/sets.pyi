from collections.abc import Set
from typing import TypeVar
from pytableaux.tools import abcs
_T_co = TypeVar('_T_co', covariant=True)

class SetView(Set[_T_co], abcs.Copyable):...