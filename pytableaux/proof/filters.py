from __future__ import annotations

import operator as opr
from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping

from pytableaux.lang.lex import (Operated, Operator, Predicated, Quantified,
                                 Sentence)
from pytableaux.proof.common import Node
from pytableaux.proof.util import Access
from pytableaux.tools import abstract, static, thru
from pytableaux.tools.abcs import Abc
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.typing import LHS, RHS

if TYPE_CHECKING:
    pass

__all__ = (
    'Filters',
    'NodeFilter',
    'NodeFilters',
)

# TODO: fix generic types on Comparer, Filters

class Comparer(Generic[LHS, RHS], Abc):

    __slots__ = 'lhs', 

    def __init__(self, lhs: LHS):
        self.lhs = lhs

    def __repr__(self):
        from pytableaux.tools.misc import orepr
        return orepr(self, lhs = self._lhsrepr(self.lhs))

    def _lhsrepr(self, lhs) -> str:
        try: return type(lhs).__qualname__
        except AttributeError: return type(lhs).__name__

    @abstract
    def __call__(self, rhs: RHS) -> bool: ...

    @abstract
    def example(self) -> RHS: ...

def getattr_safe(obj, name):
    return getattr(obj, name, None)
def getkey(obj, name):
    return obj[name]
def getkey_safe(obj, name):
    try:
        return obj[name]
    except KeyError:
        return None

@static
class Filters:

    class Attr(Comparer[LHS, RHS]):

        __slots__ = EMPTY_SET

        #: LHS attr -> RHS attr mapping.
        attrmap: Mapping[str, str] = {}

        #: Attribute getters

        lget: Callable[[LHS, str], Any] = staticmethod(getattr_safe)
        rget: Callable[[RHS, str], Any] = staticmethod(getattr)

        #: Comparison
        fcmp: Callable[[Any, Any], bool] = opr.eq

        def __call__(self, rhs: RHS, /) -> bool:
            for lattr, rattr in self.attrmap.items():
                val = self.lget(self.lhs, lattr)
                if val is not None and val != self.rget(rhs, rattr):
                    return False
            return True

        def example(self) -> dict:

            # {
            #     rattr: lvalue for lvalue, rattr in (
            #         (self.lget(self.lhs, lattr), rattr)
            #         for lattr, rattr in self.attrmap.items()
            #     )
            #     if lvalue is not None
            # }
            props = {}
            for attr, rattr in self.attrmap.items():
                val = self.lget(self.lhs, attr)
                if val is not None:
                    props[rattr] = val
            return props

    class Sentence(Comparer[LHS, RHS]):

        __slots__ = 'negated', 'applies'

        negated: bool|None

        rget: Callable[[RHS], Sentence] = thru

        def __init__(self, lhs: LHS, /, negated = None):
            super().__init__(lhs)
            if negated is None:
                self.negated = getattr(lhs, 'negated', None)
            else:
                self.negated = negated
            self.applies = any((lhs.operator, lhs.quantifier, lhs.predicate))

        def get(self, rhs: RHS, /) -> Sentence|None:
            s = self.rget(rhs)
            if s:
                if not self.negated: return s
                if isinstance(s, Operated) and s.operator is Operator.Negation:
                    return s.lhs

        def example(self) -> Sentence|None:
            if not self.applies:
                return
            lhs = self.lhs
            if lhs.operator != None:
                s = Operated.first(lhs.operator)
            elif lhs.quantifier != None:
                s = Quantified.first(lhs.quantifier)
            if lhs.negated:
                s = s.negate()
            return s

        def __call__(self, rhs: RHS, /) -> bool:
            if not self.applies: return True
            s = self.get(rhs)
            if not s: return False
            lhs = self.lhs
            if lhs.operator:
                if type(s) is not Operated or lhs.operator != s.operator:
                    return False
            if lhs.quantifier:
                if type(s) is not Quantified or lhs.quantifier != s.quantifier:
                    return False
            if lhs.predicate:
                if type(s) is not Predicated or lhs.predicate != s.predicate:
                    return False
            return True

class NodeFilter(Comparer[LHS, Node]):

    @abstract
    def example_node(self) -> dict: ...

@static
class NodeFilters(Filters):

    class Sentence(Filters.Sentence[LHS, Node], NodeFilter[LHS]):

        __slots__ = EMPTY_SET
        rhs_sentence_key = 'sentence'

        @classmethod
        def rget(cls, obj: Node) -> Sentence:
            return getkey_safe(obj, cls.rhs_sentence_key)

        def example_node(self) -> dict:
            n = {}
            s = self.example()
            if s: n['sentence'] = s
            return n

    class Designation(Filters.Attr[LHS, Node], NodeFilter[LHS]):

        __slots__ = EMPTY_SET

        attrmap = dict(designation = 'designated')
        rget: Callable[[Node], bool] = staticmethod(getkey)

        example_node = Filters.Attr.example
        # def example_node(self):
        #     return self.example()

    class Modal(Filters.Attr[LHS, Node], NodeFilter[LHS]):

        __slots__ = EMPTY_SET

        attrmap = dict(modal = 'is_modal', access = 'is_access')

        def example_node(self) -> dict:
            n = {}
            attrs = self.example()
            if attrs.get('is_access'):
                n.update(Access(0, 1)._asdict())
            elif attrs.get('is_modal'):
                n['world'] = 0
            return n
