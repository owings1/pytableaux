from __future__ import annotations

import operator as opr
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Generic, Iterable,
                    Mapping, NamedTuple, Protocol, Sequence)

from pytableaux.errors import check
from pytableaux.lang.lex import (Operated, Operator, Predicate, Predicated,
                                 Quantified, Quantifier, Sentence)
from pytableaux.proof.common import Node
from pytableaux.proof.util import Access
from pytableaux.tools import MapProxy, abstract, closure, static, thru
from pytableaux.tools.abcs import Abc
from pytableaux.tools.mappings import dmapns
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.typing import LHS, RHS, T

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'Comparer',
    'Filters',
    'NodeFilter',
    'NodeFilters',
)

EMPTY = ()
def getattr_safe(obj, name):
    return getattr(obj, name, None)
def getkey(obj, name):
    return obj[name]
def getkey_safe(obj, name):
    try:
        return obj[name]
    except KeyError:
        return None

class SentenceComparable(Protocol):

    negated    : bool|None
    operator   : Operator|None
    quantifier : Quantifier|None
    predicate  : Predicate|None

class SentenceCompItem(NamedTuple):

    type: SentenceCompType
    item: Operator|Quantifier|Predicate
    name: str
    fcmp: Callable[[Any, Any], bool]
    negated: bool

CompFuncType = Callable[[Any, Any], bool]
AttrCompItem = tuple[tuple[str, Any], ...]
SentenceCompType = type[Operated]|type[Quantified]|type[Predicated]
SentenceCompMap = tuple[tuple[str, tuple[SentenceCompType, CompFuncType]], ...]

# TODO: fix generic types on Comparer, Filters

class Comparer(Generic[LHS, RHS, T], Abc):

    __slots__ = 'compitem',

    compitem: T

    def __init__(self, *args, **kw):
        self.compitem = self._build(*args, **kw)

    def __hash__(self):
        return hash((type(self), self.compitem))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, __class__):
            return NotImplemented
        return type(self) is type(other) and self.compitem == other.compitem

    @abstract
    def __call__(self, rhs: RHS) -> bool: ...

    @abstract
    def example(self) -> RHS|Any: ...

    @classmethod
    @abstract
    def _build(cls, lhs: LHS, lget: Callable[..., Any], /) -> T:
        raise NotImplementedError

@static
class Filters:

    class Attr(Comparer[LHS, RHS, AttrCompItem]):

        #: LHS attr -> RHS attr mapping.
        attrmap: ClassVar[Mapping[str, str]] = MapProxy()

        if TYPE_CHECKING:
            @overload
            def rget(self, rhs: RHS, name: str, /) -> Any:...
            @overload
            def fcmp(self, a: Any, b: Any, /) -> bool: ...

        rget = staticmethod(getattr)
        fcmp = staticmethod(opr.eq)

        __slots__ = EMPTY_SET

        @classmethod
        def _build(cls, lhs: LHS, /, attrs: tuple[str, ...] = None, attrmap: Mapping[str, str] = None, getitem: bool = False,):
            """Build a comparison item.

            Args:
                lhs: The base object.
                attrs: Names of attributes to use. The attrmap translates into rhs name.
                attrmap: Lhs to rhs attr name mapping. Merges with class attrmap.
                getitem: Use mapping subscript to get lhs values, intead of getattr.

            Returns:
                The comparison item tuple.
            """
            if getitem:
                lget = getkey_safe
            else:
                lget = getattr_safe
            if attrs is None:
                attrs = EMPTY
            if attrmap is None:
                attrmap = MapProxy.EMPTY_MAP
            attrmap = dict(zip(attrs, attrs)) | cls.attrmap | attrmap
            trans = attrmap.get
            return tuple(
                (name, value)
                for name, value in (
                    (trans(name, name), lget(lhs, name))
                    for name in attrmap
                )
                if value is not None
            )

        def __call__(self, rhs: RHS, /) -> bool:
            rget = self.rget
            fcmp = self.fcmp
            for name, value in self.compitem:
                if not fcmp(value, rget(rhs, name)):
                    return False
            return True

        def example(self) -> RHS|dmapns[str, Any]:
            return dmapns(self.compitem)

        def __repr__(self):
            props = tuple(f'{k}={v}' for k, v in self.compitem)
            pstr = ', '.join(props)
            return f'<{type(self).__qualname__}:({pstr})>'

    class Sentence(Comparer[SentenceComparable, RHS, SentenceCompItem]):

        compmap: ClassVar[SentenceCompMap] = tuple(dict(
            operator   = (Operated, opr.is_),
            quantifier = (Quantified, opr.is_),
            predicate  = (Predicated, opr.eq),
        ).items())

        if TYPE_CHECKING:
            @staticmethod
            @overload
            def rget(rhs: RHS, /) -> Sentence|None:...
            
        rget = staticmethod(thru)

        __slots__ = EMPTY_SET

        @classmethod
        def _build(cls, lhs: SentenceComparable, /, getitem: bool = False,) -> SentenceCompItem|None:
            """Build a sentence comparison item.

            Args:
                lhs: The base object.
                getitem: Use mapping subscript to get lhs values, intead of getattr.

            Returns:
                The sentence comparison item tuple.
            """
            if getitem:
                lget = getkey_safe
            else:
                lget = getattr_safe
            for s_name, (s_type, s_fcmp) in cls.compmap:
                if (s_item := lget(lhs, s_name)) is not None:
                    s_negated = bool(lget(lhs, 'negated'))
                    break
            else:
                return None
            return SentenceCompItem(
                s_type, s_item, s_name, s_fcmp, s_negated
            )

        def sentence(self, rhs: RHS, /) -> Sentence|None:
            """Get the sentence to be examine from the rhs, or None. For a `negated`
            filter, returns the negatum, if any, else None. For a non-`negated`
            filter, returns the value retrieved unaltered.
            """
            if (s := self.rget(rhs)) is not None:
                if self.compitem.negated:
                    if type(s) is Operated and s.operator is Operator.Negation:
                        return s.lhs
                else:
                    return s

        def __call__(self, rhs: RHS, /) -> bool:
            return (compitem := self.compitem) is None or (
                type(s := self.sentence(rhs)) is compitem.type and
                compitem.fcmp(getattr(s, compitem.name), compitem.item)
            )

        def example(self) -> Sentence|None:
            if (compitem := self.compitem) is None:
                return
            s = compitem.type.first(compitem.item)
            if compitem.negated:
                s = s.negate()
            return s

        def __repr__(self):
            clsname = type(self).__qualname__
            if (compitem := self.compitem) is None:
                return f'<{clsname}:NONE>'
            nstr = '(negate)' if compitem.negated else ''
            return (
                f'<{clsname}:'
                f'{compitem.name}' '=' f'{compitem.item}' f'{nstr}''>'
            )

class NodeFilter(Comparer):

    @abstract
    def example_node(self) -> dict: ...

@static
class NodeFilters(Filters):

    class Sentence(Filters.Sentence[Node], NodeFilter):

        __slots__ = EMPTY_SET

        @staticmethod
        def rget(node: Node, /) -> Sentence|None:
            return node.get('sentence')

        def example_node(self) -> dict[str, Sentence]:
            n = {}
            s = self.example()
            if s is not None:
                n['sentence'] = s
            return n

    class Designation(Filters.Attr[LHS, Node], NodeFilter):

        attrmap = MapProxy(designation = 'designated')

        __slots__ = EMPTY_SET

        @staticmethod
        def rget(node: Node, key: str, /) -> bool:
            return node[key]

        def example_node(self) -> dict[str, bool]:
            return dict(self.example())

    class Modal(Filters.Attr[LHS, Node], NodeFilter):

        attrmap = MapProxy(modal = 'is_modal', access = 'is_access')

        __slots__ = EMPTY_SET

        def example_node(self) -> dict[str, int]:
            n = {}
            attrs = self.example()
            if attrs.get('is_access'):
                n.update(Access(0, 1)._asdict())
            elif attrs.get('is_modal'):
                n['world'] = 0
            return n
