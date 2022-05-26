from typing import (Any, Callable, ClassVar, Generic, Hashable, Mapping,
                    NamedTuple, overload)

from pytableaux.lang import Lexical, Operator, Predicate, Quantifier, Sentence
from pytableaux.proof.common import Node
from pytableaux.tools.mappings import dmapns
from pytableaux.typing import _LHS, _RHS, _T


class __SentenceComparable:
    negated: bool|None
    operator: Operator|None
    quantifier: Quantifier|None
    predicate: Predicate|None

__BoolCmFunc = Callable[[Any, Any], bool]
__Item = tuple[tuple[str, Any], ...]
__CompSentMap = tuple[tuple[str, tuple[type[Sentence], __BoolCmFunc]], ...]

class CompSentenceCompItem(NamedTuple):
    type: type[Sentence]
    item: Lexical
    name: str
    fcmp: __BoolCmFunc
    negated: bool

class Comparer(Generic[_LHS, _RHS, _T], Hashable):
    compitem: _T
    def __init__(self, *args, **kw) -> None: ...
    def __call__(self, rhs: _RHS) -> bool: ...
    def example(self) -> _RHS|Any: ...

class NodeCompare(Comparer):
    def example_node(self) -> dict: ...

class AttrCompare(Comparer[_LHS, _RHS, __Item]):
    attrmap: ClassVar[Mapping[str, str]]
    def rget(self, rhs: _RHS, name: str) -> Any: ...
    def fcmp(self, a: Any, b: Any) -> bool: ...
    def __call__(self, rhs: _RHS) -> bool: ...
    def example(self) -> _RHS|dmapns[str, Any]: ...

class SentenceCompare(Comparer[__SentenceComparable, _RHS, CompSentenceCompItem]):
    compmap: ClassVar[__CompSentMap]
    @staticmethod
    def rget(rhs: _RHS) -> Sentence|None: ...
    def sentence(self, rhs: _RHS) -> Sentence|None: ...
    def __call__(self, rhs: _RHS) -> bool: ...
    def example(self) -> Sentence|None: ...

class SentenceNode(SentenceCompare[Node], NodeCompare):
    @staticmethod
    def rget(node: Node) -> Sentence|None: ...
    def sentence(self, node: Node) -> Sentence|None: ...
    def example_node(self) -> dict[str, Sentence]: ...

class DesignationNode(AttrCompare[_LHS, Node], NodeCompare):
    @staticmethod
    def rget(node: Node, key: str) -> bool: ...
    def example_node(self) -> dict[str, bool]: ...

class ModalNode(AttrCompare[_LHS, Node], NodeCompare):
    def example_node(self) -> dict[str, int]: ...
