# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from abc import abstractmethod as abstract
from types import MappingProxyType as MapProxy
from typing import Any, Callable, Mapping, NamedTuple

from .. import __docformat__
from ..lang import (Lexical, Operated, Operator, Predicated, Quantified,
                    Sentence)
from ..tools import EMPTY_MAP, EMPTY_SET, abcs, dictns, thru
from . import WorldPair, Node
from .common import AccessNode, SentenceWorldNode, Modal

__all__ = (
    'AttrCompare',
    'Comparer',
    'DesignationNode',
    'ModalNode',
    'NodeCompare',
    'SentenceCompare',
    'SentenceNode')

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

class CompSentenceCompItem(NamedTuple):
    "Comparison parameters for a sentence filter/comparator."
    type: type[Sentence]
    "The expected sentence type."
    item: Lexical
    "The specific lexical item to match."
    name: str
    "The attribute name of the item, e.g. `'operator'`."
    fcmp: Callable
    "The comparison function for the expected item, e.g. `is` or `equals`."
    negated: bool
    "Whether the sentence must be negated."

class Comparer(abcs.Abc):
    "Filter/comparer base class."

    __slots__ = ('compitem',)

    compitem: object
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
    def __call__(self, rhs) -> bool:
        raise NotImplementedError

    @abstract
    def example(self):
        raise NotImplementedError

    @classmethod
    @abstract
    def _build(cls, *args, **kw):
        raise NotImplementedError

class NodeCompare(Comparer):
    "Node filter mixin class."

    __slots__ = EMPTY_SET

    @abstract
    def example_node(self) -> dict:
        raise NotImplementedError

class IsInstanceCompare(Comparer):
    __slots__ = EMPTY_SET
    compitem: tuple[tuple[type, ...], tuple[type, ...]]
    attrtypemap: Mapping[str, type] = EMPTY_MAP

    @classmethod
    def _build(cls, lhs) -> tuple[type, ...]:
        cmpitem = (set(), set())
        for name, ctype in cls.attrtypemap.items():
            if (value := getattr(lhs, name, None)) is not None:
                cmpitem[bool(value)].add(ctype)
        return tuple(map(tuple, cmpitem))

    def __call__(self, rhs, /) -> bool:
        falses, trues = self.compitem
        if falses and isinstance(rhs, falses):
            return False
        if trues and not isinstance(rhs, trues):
            return False
        return True

class AttrCompare(Comparer):
    "Attribute filter/comparer."

    __slots__ = EMPTY_SET

    attrmap = EMPTY_MAP
    "LHS attr -> RHS attr mapping."
    rget = staticmethod(getattr)
    fcmp = staticmethod(opr.eq)

    @classmethod
    def _build(cls, lhs, /, attrs = None, attrmap = None, getitem = False,):
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
                for name in attrmap)
            if value is not None)

    def __call__(self, rhs, /) -> bool:
        "Return whether the rhs passes the filter."
        rget = self.rget
        fcmp = self.fcmp
        for name, value in self.compitem:
            if not fcmp(value, rget(rhs, name)):
                return False
        return True

    def example(self):
        "Build an example object/mapping that satisfies the filter."
        return dictns(self.compitem)

    def __repr__(self):
        props = tuple(f'{k}={v}' for k, v in self.compitem)
        pstr = ', '.join(props)
        return f'<{type(self).__qualname__}:({pstr})>'

class SentenceCompare(Comparer):
    "Sentence filter/comparer."

    __slots__ = EMPTY_SET

    compmap = (
        *dict(
            operator   = (Operated, opr.is_),
            quantifier = (Quantified, opr.is_),
            predicate  = (Predicated, opr.eq),
        ).items(),)
        
    rget = staticmethod(thru)
    compitem: CompSentenceCompItem

    @classmethod
    def _build(cls, lhs, /, getitem = False,):
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
        return CompSentenceCompItem(s_type, s_item, s_name, s_fcmp, s_negated)

    def sentence(self, rhs):
        """Get the sentence to be examined from the rhs, or None. For a `negated`
        filter, returns the negatum, if any, else None. For a non-`negated`
        filter, returns the value retrieved unaltered.
        """
        if (s := self.rget(rhs)) is not None:
            if self.compitem.negated:
                if type(s) is Operated and s.operator is Operator.Negation:
                    return s.lhs
            else:
                return s

    def __call__(self, rhs, /) -> bool:
        "Return whether the rhs passes the filter."
        return (compitem := self.compitem) is None or (
            type(s := self.sentence(rhs)) is compitem.type and
            compitem.fcmp(getattr(s, compitem.name), compitem.item))

    def example(self):
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
        nstr = '(negated)' if compitem.negated else ''
        return (f'<{clsname}:'
            f'{compitem.name}' '=' f'{compitem.item}' f'{nstr}''>')

class SentenceNode(SentenceCompare, NodeCompare):
    "Sentence node filter."

    __slots__ = EMPTY_SET

    @staticmethod
    def rget(node: Node, /):
        return node.get(Node.Key.sentence)

    def example_node(self):
        n = {}
        s = self.example()
        if s is not None:
            n[Node.Key.sentence] = s
        return n

class DesignationNode(AttrCompare, NodeCompare):
    "Designation node filter."

    __slots__ = EMPTY_SET

    attrmap = MapProxy(dict(designation = Node.Key.designated))

    @staticmethod
    def rget(node: Node, key: str, /):
        return node[key]

    def example_node(self):
        return dict(self.example())

# class ModalNode(IsInstanceCompare, NodeCompare):
#     "Modal node filter."

#     __slots__ = EMPTY_SET

#     attrtypemap = MapProxy(dict(
#         modal = Modal,
#         access = AccessNode))

#     def example(self):
#         return dict(self.example_node())
#     def example_node(self):
#         falses, trues = self.compitem
#         if AccessNode in trues:
#             # return Node.for_mapping(Access(0, 1)._asdict())
#             return Access(0, 1).tonode()
#         if Modal in trues:
#             return SentenceWorldNode({
#                 # Node.Key.sentence: Sentence.first(),
#                 Node.Key.world: 0})
#         return Node.for_mapping({})


class ModalNode(AttrCompare, NodeCompare):
    "Modal node filter."

    __slots__ = EMPTY_SET

    attrmap = MapProxy(dict(
        modal = 'is_modal',
        access = 'is_access'))

    def example_node(self):
        n = {}
        attrs = self.example()
        if attrs.get('is_access'):
            return WorldPair(0, 1).tonode()
        elif attrs.get('is_modal'):
            return SentenceWorldNode({
                # Node.Key.sentence: Sentence.first(),
                Node.Key.world: 0})
            # n[Node.Key.world] = 0
        return n
