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

import logging
import os
import re
from collections import deque
from types import MappingProxyType as MapProxy
from typing import Any, Mapping

from ... import __docformat__
from ...lang import LexWriter, Notation
from ...proof import NodeKey
from ...tools import EMPTY_SET
from ..tableaux import Tableau
from . import TabWriter, TabWriterRegistry, nodes
from .nodes import DefaultNodeVisitor, Node, document

NOARG = object()

__all__ = (
    'HtmlDocTabWriter',
    'HtmlTranslator',
    'registry',
    'Translator')

_staticdir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'templates',
    'html',
    'static')


registry = TabWriterRegistry()

class Translator(DefaultNodeVisitor):

    format = 'unknown'

    def run(self) -> None:
        self.doc.emit(self.doc.Event.BeforeTranslate, self)
        self.doc.walkabout(self)
        self.doc.emit(self.doc.Event.AfterTranslate, self)

    def get_tagname(self, node: Node, /) -> str:
        try:
            tagname = node.tagnames[self.format]
        except KeyError:
            tagname = node.tagname
        if tagname:
            return tagname
        raise ValueError(f'tagname: {tagname}')

class HtmlTranslator(Translator):

    format = 'html'
    logger = logging.getLogger(__name__)


    from html import escape
    escape = staticmethod(escape)

    def __init__(self, doc: document, lw: LexWriter, /):
        super().__init__(doc)
        self.head: deque[str] = deque()
        self.body: deque[str] = deque()
        self.foot: deque[str] = deque()
        self.lw = lw

    def visit_document(self, node: Node, /):
        raise nodes.SkipDeparture

    def visit_textnode(self, node: Node, /):
        self.body.append(self.escape(node))
        raise nodes.SkipDeparture

    def visit_rawtext(self, node: Node, /):
        self.body.append(node)
        raise nodes.SkipDeparture

    def visit_sentence(self, node: Node, /):
        self.default_visitor(node)
        rendered = self.lw(node[NodeKey.sentence])
        if self.lw.charset != self.format:
            rendered = self.escape(rendered)
        self.body.append(rendered)

    def get_attrs_map(self, node: Node, /) -> dict[str, str]:
        attrs = {}
        todo = dict(node.attributes)
        if todo.get('id'):
            attrs['id'] = str(todo.pop('id'))
        if todo.get('class'):
            todo['classes'].add(str(todo.pop('class')))
        if todo['classes']:
            attrs['class'] = ' '.join(
                re.sub(r'[\r]+', ' ', c).strip()
                for c in todo.pop('classes'))
        for key in sorted(todo):
            value = todo.pop(key)
            if isinstance(value, (str, int, float, bool)):
                attrs[key] = str(value)
            else:
                self.logger.warning(
                    f'Not writing {key} attribute of type {type(value)}')
        return attrs

    def get_attrs_str(self, attrs: Mapping[str, Any]) -> str:
        return ' '.join(
            f'{self.escape(k)}="{self.escape(v)}"'
            for k, v in attrs.items())

    def write_opentag(self, tagname: str, attrs: Mapping[str, Any]) -> None:
        self.body.append(' '.join(filter(None, (
            f'<{self.escape(tagname)}',
            self.get_attrs_str(attrs)))) + '>')

    def write_closetag(self, tagname: str) -> None:
        self.body.append(f'</{self.escape(tagname)}>')

    def default_visitor(self, node: Node, /):
        self.write_opentag(self.get_tagname(node), self.get_attrs_map(node))

    def default_departer(self, node: Node, /):
        self.write_closetag(self.get_tagname(node))


@registry.register
class HtmlDocTabWriter(TabWriter):

    __slots__ = EMPTY_SET

    format = 'html'
    css_template_name = 'tableau.css'
    default_charsets = MapProxy({
        notn: 'html' for notn in Notation})
    defaults = MapProxy(dict(
        wrapper      = True,
        classes      = (),
        wrap_classes = (),
        inline_css   = False))
    node_types = MapProxy(dict(
        document = nodes.document,
        style    = nodes.style,
        rawtext  = nodes.rawtext,
        tableau  = nodes.tableau,
        wrapper  = nodes.wrapper,
        clear    = nodes.clear))
    _CSS_CACHE = None

    def __call__(self, tab: Tableau, *, classes=None, wrap_classes=None):
        types = self.node_types
        doc = types['document']()
        if self.opts['wrapper']:
            wrap = types['wrapper'](classes=['tableau_wrapper'])
            wrap['classes'] |= wrap_classes or EMPTY_SET
            wrap['classes'] |= self.opts['wrap_classes']
            doc += wrap
        else:
            wrap = doc
        if self.opts['inline_css']:
            css = '\n' + self.attachments()['css'] + '\n'
            wrap += types['style'](types['rawtext'](css))
        node = types['tableau'].for_object(tab)
        node['classes'] |= classes or EMPTY_SET
        node['classes'] |= self.opts['classes']
        wrap += node, types['clear']()
        translator = HtmlTranslator(doc, self.lw)
        translator.run()
            
        return ''.join(translator.body)

    def attachments(self, /):
        cls = type(self)
        cssfile = f'{_staticdir}/{self.css_template_name}'
        if not cls._CSS_CACHE or cls._CSS_CACHE[0] != cssfile:
            with open(cssfile) as f:
                cls._CSS_CACHE = cssfile, f.read().replace('<', '&lt;')
        return dict(css=cls._CSS_CACHE[1])