
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
pytableaux.proof.writers.elements
=================================

"""
from __future__ import annotations

from typing import Any, Callable, Iterable, SupportsIndex

from ...errors import check
from ...tools import EMPTY_MAP, EMPTY_QSET, EMPTY_SET, TransMmap, qset, qsetf


class Attributes(TransMmap[str, Any]):

    def __init__(self, *args, **kw):
        super().__init__(kget=str.lower, kset=str.lower)
        self.update(*args, **kw)

class Node:

    parent: Node|None = None
    children: qset[Node] = EMPTY_QSET
    attributes: TransMmap[str, Any] = EMPTY_MAP
    tagname = None
    _document = None

    @property
    def document(self) -> Document|None:
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
    def document(self, value: Document):
        self._document = value

    def setup_child(self, child: Node):
        child.parent = self
        if self.document:
            child.document = self.document
        return child

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.attributes[key]
        return self.children[check.inst(key, (SupportsIndex, slice))]

    def __bool__(self):
        return True

    def walk(self, visit: Callable[[Node], None], depart: Callable[[Node], None]|None = None):
        visit(self)
        for child in self.children[:]:
            child.walk(visit, depart)
        if depart:
            depart(self)

    def walkabout(self, visitor: NodeVisitor, /):
        self.walk(visitor.dispatch_visit, visitor.dispatch_departure)

    def iterate(self):
        yield self
        for child in self.children[:]:
            yield from child.iterate()

class Element(Node):

    default_classes = EMPTY_SET
    default_attributes = EMPTY_MAP
    sequence_attributes = frozenset(('ids', 'names', 'classes'))


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
            classes = (name.replace('_', '-'),)
        if not isinstance(classes, qsetf):
            classes = qsetf(classes)
        cls.default_classes = classes


class Document(Element):

    @property
    def document(self):
        return self

class Block(Element):
    pass

class Inline(Element):
    pass

class NodeVisitor:

    def dispatch_visit(self, node: Node):
        raise NotImplementedError

    def dispatch_departure(self, node: Node):
        raise NotImplementedError