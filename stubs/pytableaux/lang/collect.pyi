from typing import Callable, Hashable, Iterable, SupportsIndex, overload

from _typeshed import SupportsRichComparison as _SupportsRichCompare
from pytableaux.lang import LangCommonMeta, Predicate, Sentence
from pytableaux.tools import qset
from pytableaux.tools.sequences import SequenceApi

pass

from pytableaux.lang.lex import _PredicateSpec


class ArgumentMeta(LangCommonMeta):...

class Argument(SequenceApi[Sentence], _SupportsRichCompare, Hashable, metaclass=ArgumentMeta):
    seq: tuple[Sentence,...]
    title: str|None
    premises:tuple[Sentence,...]
    @property
    def conclusion(self) -> Sentence: ...
    @property
    def hash(self) -> int: ...
    def __init__(self, conclusion: Sentence, premises: Iterable[Sentence]|None = ..., title: str = ...) -> None: ...
    def predicates(self, **kw) -> Predicates: ...
    @overload
    def __getitem__(self, s: slice) -> tuple[Sentence, ...]: ...
    @overload
    def __getitem__(self, i: SupportsIndex) -> Sentence: ...
    def for_json(self) -> dict[str, Sentence|tuple[Sentence, ...]]: ...

class Predicates(qset[Predicate], metaclass=LangCommonMeta):
    def __init__(self, values: Iterable[_PredicateSpec | Predicate] = ..., *, sort: bool = ..., key: Callable | None = ..., reverse: bool = ...) -> None: ...
    def get(self, ref: _PredicateSpec | Predicate, default=...) -> Predicate: ...
    def specs(self) -> tuple[_PredicateSpec, ...]: ...
    def clear(self) -> None: ...
