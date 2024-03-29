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
pytableaux.proof.writers.doctree
================================

"""
from __future__ import annotations

import itertools
from abc import abstractmethod
from collections import deque
from types import MappingProxyType as MapProxy
from typing import Any, Callable, Self, TypeVar

from ....lang import LexWriter, StringTable
from ....tools import EMPTY_SET, abcs
from ...tableaux import Tableau
from .. import TabWriter, TabWriterRegistry
from . import nodes

_NT = TypeVar('_NT', bound='nodes.Node')

__all__ = (
    'DefaultNodeVisitor',
    'DoctreeTabWriter',
    'NodeVisitor',
    'registry',
    'Translator')

NOARG = object()

class NodeVisitor(abcs.Abc):

    __slots__ = EMPTY_SET

    def dispatch_visit(self, node: nodes.Node):
        try:
            func = self.find_visitor(node)
        except AttributeError:
            raise NotImplementedError
        func(node)

    def dispatch_departure(self, node: nodes.Node):
        try:
            func = self.find_departer(node)
        except AttributeError:
            raise NotImplementedError
        func(node)

    def find_visitor(self, node: _NT, /) -> Callable[[_NT], None]:
        return getattr(self, f'visit_{type(node).__name__}')

    def find_departer(self, node: _NT, /) -> Callable[[_NT], None]:
        return getattr(self, f'depart_{type(node).__name__}')

class DefaultNodeVisitor(NodeVisitor):

    __slots__ = EMPTY_SET

    def find_visitor(self, node, /):
        try:
            return super().find_visitor(node)
        except AttributeError:
            return self.default_visitor

    def find_departer(self, node, /):
        try:
            return super().find_departer(node)
        except AttributeError:
            return self.default_departer

    @abstractmethod
    def default_visitor(self, node: nodes.Node, /):
        raise NotImplementedError

    @abstractmethod
    def default_departer(self, node: nodes.Node, /):
        raise NotImplementedError

class Translator(abcs.Abc):

    format = 'unknown'

    doc: nodes.document
    head: deque[str]
    body: deque[str]
    foot: deque[str]
    lw: LexWriter
    strings: StringTable

    def __init__(self, doc: nodes.document, lw: LexWriter, /):
        self.doc = doc
        self.head = deque()
        self.body = deque()
        self.foot = deque()
        self.lw = lw
        if self.lw.format == self.format:
            self.strings = self.lw.strings
        else:
            self.strings = StringTable.fetch(
                notation=self.lw.notation,
                format=self.format)
        self.setup()

    def setup(self):
        pass

    def translate(self) -> None:
        self.doc.walkabout(self)

    def __iadd__(self, item: Any) -> Self:
        if isinstance(item, str):
            self.body.append(item)
        else:
            self.body.extend(item)
        return self

class DoctreeTabWriter(TabWriter):

    __slots__ = EMPTY_SET

    engine = 'doctree'
    docnode_type: type[nodes.document] = nodes.document
    translator_type: type[Translator]
    defaults = MapProxy(dict(
        fulldoc = False))

    def __call__(self, tab: Tableau, *, fulldoc=None, **kw):
        doc = self.build_doc(tab, **kw)
        return self.render(doc, fulldoc=fulldoc)

    @abstractmethod
    def build_doc(self, tab: Tableau, /) -> nodes.document:
        types = self.docnode_type.types
        return types[nodes.document](types[nodes.tableau].for_object(tab))

    def render(self, doc: nodes.document, /, *, fulldoc=None) -> str:
        if fulldoc is None:
            fulldoc = self.opts['fulldoc']
        translator = self.translator_type(doc, self.lw)
        translator.translate()
        parts = deque()
        if fulldoc:
            parts.append(translator.head)
        parts.append(translator.body)
        if fulldoc:
            parts.append(translator.foot)
        return ''.join(itertools.chain.from_iterable(parts))

registry = TabWriterRegistry(name=DoctreeTabWriter.engine)

from .html import HtmlTabWriter as HtmlTabWriter
from .latex import LatexTabWriter as LatexTabWriter
from .text import TextTabWriter as TextTabWriter

registry.register(HtmlTabWriter)
registry.register(LatexTabWriter)
