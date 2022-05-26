from typing import Generator, Mapping

from pytableaux.lang import Argument, Predicates
from pytableaux.logics import Registry
from pytableaux.proof import Tableau
from pytableaux.typing import _LogicLookupKey

data: Mapping[str, tuple[tuple[str, ...], str]]
aliases: Mapping[str, tuple[str, ...]]
titles: tuple[str, ...]
preds: Predicates

def argument(key: str|Argument) -> Argument:...
def arguments(*keys: str|Argument) -> tuple[Argument, ...]: ...
def tabiter(*logics: _LogicLookupKey, build:bool = ..., grouparg: bool = ..., registry: Registry = ..., **opts) -> Generator[None, None, Tableau]: ...
