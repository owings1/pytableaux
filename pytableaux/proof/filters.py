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
pytableaux.proof.filters
^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import operator as opr
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Generic, Mapping,
                    NamedTuple)

from pytableaux import __docformat__
from pytableaux.lang.lex import (Operated, Operator, Predicate, Predicated,
                                 Quantified, Quantifier, Sentence)
from pytableaux.proof.common import Node
from pytableaux.proof.util import Access
from pytableaux.tools import EMPTY_MAP, MapProxy, abstract, thru
from pytableaux.tools.abcs import Abc
from pytableaux.tools.mappings import dmapns
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.typing import LHS, RHS, T

if TYPE_CHECKING:
    from typing import overload

    class SentenceComparable:

        negated    : bool|None
        operator   : Operator|None
        quantifier : Quantifier|None
        predicate  : Predicate|None
else:
    SentenceComparable = object

__all__ = (
    'AttrCompare',
    'Comparer',
    'DesignationNode',
    'ModalNode',
    'NodeCompare',
    'SentenceCompare',
    'SentenceNode',
)

def getattr_safe(obj: Any, name: str) -> Any:
    return getattr(obj, name, None)

def getkey(obj: Any, key: Any) -> Any:
    return obj[key]

def getkey_safe(obj: Any, key: Any) -> Any:
    try:
        return obj[key]
    except KeyError:
        return None

# class SkipFilter(Exception): pass

BoolCompFunc = Callable[[Any, Any], bool]
"Function that returns a boolean for any two arguments."

CompAttrCompItem = tuple[tuple[str, Any], ...]
"The `compitem` type for `Attr` comparer."

CompSentenceType = type[Operated]|type[Quantified]|type[Predicated]
"Union of possible expected sentence types."

CompSentenceMap = tuple[tuple[str, tuple[CompSentenceType, BoolCompFunc]], ...]
"The type for the reference data for building sentence comp items."

class CompSentenceCompItem(NamedTuple):
    "Comparison parameters for a sentence filter/comparator."

    type: CompSentenceType
    "The expected sentence type."

    item: Operator|Quantifier|Predicate
    "The specific lexical item to match."

    name: str
    "The attribute name of the item, e.g. `'operator'`."

    fcmp: BoolCompFunc
    "The comparison function for the expected item, e.g. `is` or `equals`."

    negated: bool
    "Whether the sentence must be negated."

class Comparer(Generic[LHS, RHS, T], Abc):
    "Filter/comparer base class."

    __slots__ = 'compitem',

    compitem: T
    "The hashable comparison item tuple."

    def __init__(self, *args, **kw):
        self.compitem = self._build(*args, **kw)

    def __hash__(self):
        return hash((type(self), self.compitem))

    def __eq__(self, other):
        if self is other:
            return True
        if type(self) is type(other):
            return self.compitem == other.compitem
        if isinstance(other, __class__):
            return False
        return NotImplemented

    @abstract
    def __call__(self, rhs: RHS) -> bool:
        raise NotImplementedError

    @abstract
    def example(self) -> RHS|Any:
        raise NotImplementedError

    @classmethod
    @abstract
    def _build(cls, lhs: LHS, lget: Callable[..., Any], /) -> T:
        raise NotImplementedError

class NodeCompare(Comparer):
    "Node filter mixin class."

    @abstract
    def example_node(self) -> dict: ...

class AttrCompare(Comparer[LHS, RHS, CompAttrCompItem]):
    "Attribute filter/comparer."

    attrmap: ClassVar[Mapping[str, str]] = EMPTY_MAP
    "LHS attr -> RHS attr mapping."

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
            attrs = EMPTY_SET
        if attrmap is None:
            attrmap = EMPTY_MAP
        attrmap = dict(zip(attrs, attrs)) | cls.attrmap | attrmap
        trans = attrmap.get
        return tuple(
            (trans(name, name), value)
            for name, value in (
                (name, lget(lhs, name))
                for name in attrmap
            )
            if value is not None
        )

    def __call__(self, rhs: RHS, /) -> bool:
        "Return whether the rhs passes the filter."
        rget = self.rget
        fcmp = self.fcmp
        for name, value in self.compitem:
            if not fcmp(value, rget(rhs, name)):
                return False
        return True

    def example(self) -> RHS|dmapns[str, Any]:
        "Build an example object/mapping that satisfies the filter."
        return dmapns(self.compitem)

    def __repr__(self):
        props = tuple(f'{k}={v}' for k, v in self.compitem)
        pstr = ', '.join(props)
        return f'<{type(self).__qualname__}:({pstr})>'

class SentenceCompare(Comparer[SentenceComparable, RHS, CompSentenceCompItem]):
    "Sentence filter/comparer."

    compmap: ClassVar[CompSentenceMap] = (
        *dict(
            operator   = (Operated, opr.is_),
            quantifier = (Quantified, opr.is_),
            predicate  = (Predicated, opr.eq),
        ).items(),
    )

    if TYPE_CHECKING:

        @staticmethod
        @overload
        def rget(rhs: RHS, /) -> Sentence|None: ...
        
    rget = staticmethod(thru)

    __slots__ = EMPTY_SET

    @classmethod
    def _build(cls, lhs: SentenceComparable, /, getitem: bool = False,) -> CompSentenceCompItem|None:
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
        return CompSentenceCompItem(
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
        "Return whether the rhs passes the filter."
        return (compitem := self.compitem) is None or (
            type(s := self.sentence(rhs)) is compitem.type and
            compitem.fcmp(getattr(s, compitem.name), compitem.item)
        )

    def example(self) -> Sentence|None:
        "Construct an example sentence that matches the filter conditions."
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

class SentenceNode(SentenceCompare[Node], NodeCompare):
    "Sentence node filter."

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

class DesignationNode(AttrCompare[LHS, Node], NodeCompare):
    "Designation node filter."

    attrmap = MapProxy(dict(
        designation = 'designated',
    ))

    __slots__ = EMPTY_SET

    @staticmethod
    def rget(node: Node, key: str, /) -> bool:
        return node[key]

    def example_node(self) -> dict[str, bool]:
        return dict(self.example())

class ModalNode(AttrCompare[LHS, Node], NodeCompare):
    "Modal node filter."

    attrmap = MapProxy(dict(
        modal = 'is_modal',
        access = 'is_access',
    ))

    __slots__ = EMPTY_SET

    def example_node(self) -> dict[str, int]:
        n = {}
        attrs = self.example()
        if attrs.get('is_access'):
            n.update(Access(0, 1)._asdict())
        elif attrs.get('is_modal'):
            n['world'] = 0
        return n
