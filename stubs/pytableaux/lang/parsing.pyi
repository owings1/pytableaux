import abc
from collections.abc import Set
from typing import Any, ClassVar, Iterable, Mapping, overload

from pytableaux.lang import (Argument, LangCommonMeta, Lexical, LexType,
                             Marking, Notation, Predicate, Predicates,
                             Sentence, TableStore, Variable)
from pytableaux.tools import abcs
from pytableaux.tools.mappings import MapCover
from pytableaux.tools.sequences import seqf
from pytableaux.typing import _Self

_ParseTableValue = int|Lexical
_ParseTableKey   = LexType|Marking|type[Predicate.System]

class ParserMeta(LangCommonMeta):...

class Parser(metaclass=ParserMeta):
    notation: ClassVar[Notation]
    table: ParseTable
    preds: Predicates
    opts: Mapping[str, Any]
    def __init__(self, preds: Predicates = ..., table: ParseTable|str = ..., **opts) -> None: ...
    def parse(self, input_: str) -> Sentence: ...
    def __call__(self, input_: str) -> Sentence: ...
    def argument(self, conclusion: str, premises: Iterable[str] = ..., title: str = ...) -> Argument: ...

class ParseContext:
    bound: set[Variable]
    input: str
    preds: Predicates
    is_open: bool
    pos: int
    def __init__(self, input_: str, table: ParseTable, preds: Predicates) -> None: ...
    def __enter__(self): ...
    def __exit__(self, typ, value, traceback) -> None: ...
    def current(self) -> str|None: ...
    def next(self, n: int = ...) -> str|None: ...
    def assert_current(self) -> _ParseTableKey|None: ...
    def assert_current_is(self, ctype: _ParseTableKey) -> None: ...
    def assert_current_in(self, ctypes: Set[_ParseTableKey]) -> _ParseTableKey: ...
    def assert_end(self) -> None: ...
    def has_next(self, n: int = ...) -> bool: ...
    def has_current(self) -> bool: ...
    def advance(self:_Self, n: int = ...) -> _Self: ...
    def chomp(self) -> ParseContext: ...
    def type(self, char: str, default=...) -> _ParseTableKey: ...

class Ctype(frozenset[_ParseTableKey], abcs.Ebc):
    pred: frozenset
    base: frozenset
    param: frozenset

class BaseParser(Parser, metaclass=abc.ABCMeta):...
class PolishParser(BaseParser):...
class StandardParser(BaseParser):...
class ParseTable(MapCover[str, tuple[_ParseTableKey, _ParseTableValue]], TableStore, metaclass=abc.ABCMeta):
    reversed: Mapping[tuple[_ParseTableKey, _ParseTableValue], str]
    chars: Mapping[_ParseTableKey, seqf[str]]
    keypair: tuple[Notation, str]
    @property
    def notation(self) -> Notation: ...
    @property
    def fetchkey(self) -> str: ...
    def __init__(self, data: Mapping[str, tuple[_ParseTableKey, _ParseTableValue]], keypair: tuple[Notation, str]) -> None: ...
    def type(self, char: str, default=...) -> _ParseTableKey: ...
    def value(self, char: str) -> _ParseTableValue: ...
    def char(self, ctype: _ParseTableKey, value: _ParseTableValue) -> str: ...
