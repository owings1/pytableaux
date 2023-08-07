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
pytableaux.proof.writers.nodes
==============================

"""
from __future__ import annotations

import enum
from abc import abstractmethod
from enum import Enum
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Generic, Iterable,
                    Mapping, Self, Sequence, SupportsIndex, TypeVar)

from ... import proof
from ...errors import check
from ...tools import (EMPTY_MAP, EMPTY_QSET, EMPTY_SET, TransMmap, abcs, qset,
                      qsetf)
from ...tools.events import EventEmitter
from .. import Access, NodeAttr, NodeKey, Tableau

__all__ = (
    'access',
    'child_wrapper',
    'clear',
    'designation',
    'document',
    'ellipsis',
    'flag',
    'horizontal_line',
    'node_props',
    'node_segment',
    'node',
    'sentence',
    'tree',
    'vertical_line',
    'world')

if TYPE_CHECKING:
    from .nodes import NodeVisitor
    from .doctree import Translator

_T = TypeVar('_T')
_NT = TypeVar('_NT', bound='Node')

class TreePruningException(Exception): pass
class SkipDeparture(TreePruningException): pass

class Attributes(TransMmap[str, Any]):

    def __init__(self, *args, **kw):
        super().__init__(kget=str.lower, kset=str.lower)
        self.update(*args, **kw)

class TranslatorAware:
    "Class to flag for doc modifications before translating"

    @abstractmethod
    def before_translate(self, trans: Translator, doc: document, /) -> None:
        pass

class ObjectBuilder(Generic[_T]):

    @classmethod
    def for_object(cls, obj: _T, /) -> Self:
        return cls(
            *cls.get_obj_args(obj),
            classes=cls.get_obj_classes(obj),
            **dict(cls.get_obj_attributes(obj)))

    @classmethod
    def get_obj_args(cls, obj: _T, /) -> Iterable[Any]:
        yield from cls.get_obj_children(obj)

    @classmethod
    def get_obj_children(cls, obj: _T, /) -> Iterable[Node]:
        yield from EMPTY_SET

    @classmethod
    def get_obj_classes(cls, obj: _T, /) -> Iterable[str]:
        yield from EMPTY_SET

    @classmethod
    def get_obj_attributes(cls, obj: _T, /) -> Iterable[tuple[str, Any]]:
        yield from EMPTY_SET

class Node(abcs.Abc):

    tagnames: ClassVar[Mapping[str, str]] = EMPTY_MAP
    tagname: ClassVar[str|None] = None

    parent: Node|None
    children: qset[Node]
    attributes: TransMmap[str, Any]

    @property
    def document(self) -> document|None:
        try:
            doc = self._document
            if doc:
                return doc
            doc = self.parent.document
            if doc:
                self.document = doc
            return doc
        except AttributeError:
            return None

    @document.setter
    def document(self, value: document):
        self._document = value

    def setup_child(self, child: Node):
        child.parent = self
        if self.document:
            child.document = self.document
        return child

    def __bool__(self):
        return True

    def walk(self, visit: Callable[[Node], None], depart: Callable[[Node], None]|None = None):
        is_depart = True
        try:
            visit(self)
        except SkipDeparture:
            is_depart = False
        for child in self.children[:]:
            child.walk(visit, depart)
        if is_depart and depart:
            depart(self)

    def walkabout(self, visitor: NodeVisitor, /):
        self.walk(visitor.dispatch_visit, visitor.dispatch_departure)

    def iterate(self):
        yield self
        for child in self.children[:]:
            yield from child.iterate()

class Text(Node, str):
    tagname = '#text'
    children = EMPTY_QSET

class Element(Node):

    default_classes: ClassVar[Sequence[str]] = EMPTY_QSET
    default_attributes: ClassVar[Mapping[str, Any]] = EMPTY_MAP
    sequence_attributes: ClassVar[Sequence[str]] = frozenset({'classes'})

    def __init__(self, *children, **attributes):
        self.children = qset()
        self.attributes = Attributes(
            (name, qset(attributes.pop(name, EMPTY_SET)))
            for name in self.sequence_attributes)
        self |= self.default_attributes
        self |= attributes
        self['classes'] |= self.default_classes
        self += children

    def append(self, child: Node):
        self.children.append(self.setup_child(child))

    def extend(self, children: Iterable[Node]):
        self.children.extend(map(self.setup_child, children))

    def update(self, *args, **kw):
        self.attributes.update(*args, **kw)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.attributes[key]
        return self.children[check.inst(key, (SupportsIndex, slice))]

    get = Mapping.get

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.attributes[key] = value
        elif isinstance(key, SupportsIndex):
            self.children[key] = self.setup_child(value)
        else:
            raise TypeError(f'slice not yet supported')
            # self.children[check.inst(key, slice)] = list(map(self.setup_child, value))

    def __delitem__(self, key):
        if isinstance(key, str):
            del self.attributes[key]
        else:
            del self.children[check.inst(key, (SupportsIndex, slice))]

    def __iadd__(self, other):
        if isinstance(other, Node):
            self.append(other)
        elif other is not None:
            self.extend(other)
        return self

    def __ior__(self, other):
        self.update(other)
        return self

    def __len__(self):
        return len(self.children)

    def __contains__(self, key):
        if isinstance(key, str):
            return key in self.attributes
        return key in self.children

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        name = cls.__name__
        if name.lower() != name:
            return
        if cls.tagname is None:
            cls.tagname = name
        classes = cls.default_classes
        if not classes:
            if classes is False:
                classes = EMPTY_QSET
            else:
                classes = [name.replace('_', '-')]
        if not isinstance(classes, qsetf):
            classes = qsetf(classes)
        cls.default_classes = classes

class InlineElement(Element):
    tagnames = MapProxy(dict(html='span'))

class BlockElement(Element):
    tagnames = MapProxy(dict(html='div'))


class textnode(Text): pass
class rawtext(Text): pass
class subscript(Element):
    tagnames = MapProxy(dict(html='sub'))
    default_classes = False
class style(Element):
    default_classes = False

class clear(BlockElement): pass
class ellipsis(InlineElement, ObjectBuilder[proof.Node]): pass

class wrapper(BlockElement):
    default_classes = False

class vertical_line(BlockElement, ObjectBuilder[int]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield 'data-step', obj

class horizontal_line(BlockElement, ObjectBuilder[Tableau.Tree]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield 'data-step', obj.branch_step
        width = 100 * obj.balanced_line_width
        margin_left = 100 * obj.balanced_line_margin
        yield 'style', _styleattr(
            width=_pctstr(width),
            margin_left=_pctstr(margin_left))

class child_wrapper(BlockElement, ObjectBuilder[tuple[Tableau.Tree, Tableau.Tree]]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        tree, child = obj
        width = (100 / tree.width) * child.width
        yield 'data-step', child.step
        yield 'data-current-width-pct', _pctstr(width)
        yield 'style', _styleattr(width=_pctstr(width))

class sentence(InlineElement, ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield NodeKey.sentence, obj[NodeKey.sentence]

class world(InlineElement, ObjectBuilder[proof.Node], TranslatorAware):

    node_types = MapProxy(dict(
        subscript=subscript,
        textnode=textnode))

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield NodeKey.world, obj[NodeKey.world]

    def before_translate(self, trans, doc, /):
        if trans.format != 'html':
            return
        types = self.node_types
        textnode = types['textnode']
        self += textnode(', w')
        self += types['subscript'](textnode(self['world']))

class designation(InlineElement, ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_classes(cls, obj, /):
        if obj.get(NodeKey.designation):
            yield 'designated'
        else:
            yield 'undesignated'

class access(InlineElement, ObjectBuilder[proof.Node], TranslatorAware):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield from Access.fornode(obj).tonode().items()

    def before_translate(self, trans, doc, /):
        if trans.format != 'html':
            return
        
class flag(InlineElement, ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_classes(cls, obj, /):
        yield obj[NodeKey.flag]

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield NodeKey.info, obj.get(NodeKey.info, '')

class node_props(InlineElement, ObjectBuilder[proof.Node]):

    node_types = MapProxy({
        NodeKey.sentence: sentence,
        NodeKey.world: world,
        NodeKey.designation: designation,
        NodeAttr.is_access: access,
        NodeKey.ellipsis: ellipsis,
        NodeKey.is_flag: flag})

    @classmethod
    def get_obj_classes(cls, obj, /):
        if getattr(obj, NodeAttr.ticked, False):
            yield 'ticked'

    @classmethod
    def get_obj_children(cls, obj, /):
        types = cls.node_types
        if obj.has(NodeKey.sentence):
            yield types[NodeKey.sentence].for_object(obj)
            if obj.has(NodeKey.world):
                yield types[NodeKey.world].for_object(obj)
        if obj.has(NodeKey.designation):
            yield types[NodeKey.designation].for_object(obj)
        if getattr(obj, NodeAttr.is_access):
            yield types[NodeAttr.is_access].for_object(obj)
        if obj.has(NodeKey.ellipsis):
            yield types[NodeKey.ellipsis].for_object(obj)
        if obj.has(NodeKey.is_flag):
            yield types[NodeKey.is_flag].for_object(obj)

class node(BlockElement, ObjectBuilder[tuple[proof.Node, int]]):

    node_types = MapProxy(dict(node_props=node_props))

    @classmethod
    def get_obj_attributes(cls, obj, /):
        node, tickstep = obj
        yield 'id', f'node_{node.id}'
        yield 'data-node-id', node.id
        yield 'data-step', node.step
        if getattr(node, NodeAttr.ticked, None):
            yield 'data-ticked-step', tickstep

    @classmethod
    def get_obj_classes(cls, obj, /):
        if getattr(obj[0], NodeAttr.ticked, None):
            yield 'ticked'

    @classmethod
    def get_obj_children(cls, obj, /):
        yield cls.node_types['node_props'].for_object(obj[0])

class node_segment(BlockElement, ObjectBuilder[Tableau.Tree]):

    node_types = MapProxy(dict(
        node=node,
        vertical_line=vertical_line))

    @classmethod
    def get_obj_children(cls, obj, /):
        types = cls.node_types
        if not obj.root:
            yield types['vertical_line'].for_object(obj.step)
        yield from map(
            types['node'].for_object,
            zip(obj.nodes, obj.ticksteps))

class tree(BlockElement, ObjectBuilder[Tableau.Tree]):

    default_classes = ['structure']

    data_attrnames = (
        'depth',
        'width',
        'left',
        'right',
        'step')

    flag_classnames = (
        'has_open',
        'has_closed',
        'leaf',
        'open',
        'closed',
        'is_only_branch')

    node_types = MapProxy(dict(
        (cls.__name__, cls) for cls in (
            node_segment,
            vertical_line,
            horizontal_line,
            child_wrapper)))

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield 'id', f'structure_{obj.id}'
        for name in cls.data_attrnames:
            yield f'data-{name}', obj[name]
        if obj.closed:
            yield 'data-closed-step', obj.closed_step
        if obj.branch_id:
            yield 'data-branch-id', obj.branch_id
        if obj.model_id:
            yield 'data-model-id', obj.model_id
        
    @classmethod
    def get_obj_classes(cls, obj, /):
        if obj.root:
            yield 'root'
        yield from filter(obj.get, cls.flag_classnames)

    @classmethod
    def get_obj_children(cls, obj, /):
        types = cls.node_types
        node = types['node_segment'].for_object(obj)
        if obj.children:
            node += types['vertical_line'].for_object(obj.branch_step)
            node += types['horizontal_line'].for_object(obj)
            for child in obj.children:
                wrap = types['child_wrapper'].for_object((obj, child))
                wrap += cls.for_object(child)
                node += wrap
        yield node

class tableau(BlockElement, ObjectBuilder[Tableau]):

    node_types = MapProxy(dict(tree=tree))

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield from {
            'id': f'tableau_{obj.id}',
            'data-step': len(obj.history),
            'data-num-steps': len(obj.history),
            'data-current-width-pct': 100}.items()

    @classmethod
    def get_obj_children(cls, obj, /):
        yield cls.node_types['tree'].for_object(obj.tree)

class document(Element, EventEmitter):

    class Event(enum.Enum):
        BeforeTranslate = enum.auto()
        AfterTranslate = enum.auto()

    @property
    def document(self):
        return self

    def __init__(self, *args, **kw):
        EventEmitter.__init__(self, *self.Event)
        super().__init__(*args, **kw)
        self.on(self.Event.BeforeTranslate, self.__before_translate)

    # Avoid EventEmitter copy implementation.
    copy = NotImplemented

    def __before_translate(self, trans: Translator, /):
        for node in self.iterate():
            if isinstance(node, TranslatorAware):
                node.before_translate(trans, self)
        for node in self.iterate():
            if node is not self:
                node.document = self


class NodeVisitor(abcs.Abc):

    @abstractmethod
    def dispatch_visit(self, node: Node):
        raise NotImplementedError

    @abstractmethod
    def dispatch_departure(self, node: Node):
        raise NotImplementedError

class DefaultNodeVisitor(NodeVisitor):

    def __init__(self, doc: document, /):
        self.doc = doc

    def dispatch_visit(self, node):
        cls = type(node)
        self.find_visitor(cls.__name__, cls, node)(node)

    def dispatch_departure(self, node):
        cls = type(node)
        self.find_departer(cls.__name__, cls, node)(node)

    def find_visitor(self, clsname: str, cls: type[_NT], node: _NT, /) -> Callable[[_NT], None]:
        try:
            return getattr(self, f'visit_{clsname}')
        except AttributeError:
            return self.default_visitor

    def find_departer(self, clsname: str, cls: type[_NT], node: _NT, /) -> Callable[[_NT], None]:
        try:
            return getattr(self, f'depart_{clsname}')
        except AttributeError:
            return self.default_departer

    @abstractmethod
    def default_visitor(self, node: Node, /):
        raise NotImplementedError

    @abstractmethod
    def default_departer(self, node: Node, /):
        raise NotImplementedError


def _styleattr(*args, **kw):
    return ' '.join(
        f"{str(key).replace('_', '-')}: {value};"
        for key, value in dict(*args, **kw).items())

def _uscore(s: str):
    return s.replace('-', '_')

def _endash(s: str):
    return s.replace('_', '-')

def _pctstr(n):
    return f'{n}%'