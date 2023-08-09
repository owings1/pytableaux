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

import html
import logging
import os
import re
from collections import deque
from types import MappingProxyType as MapProxy
from typing import Any, Mapping

from ....lang import LexWriter, Notation
from ....proof import NodeKey
from ....tools import EMPTY_SET
from ...tableaux import Tableau
from ..jinja import TEMPLATES_BASE_DIR, jinja
from .. import TabWriter, TabWriterRegistry
from . import nodes

NOARG = object()

__all__ = (
    'HtmlTabWriter',
    'HtmlTranslator',
    'registry',
    'Translator')

registry = TabWriterRegistry(name='doctree')

class DoctreeTabWriter(TabWriter):

    __slots__ = EMPTY_SET

    engine = 'doctree'
    doc_nodetype: type[nodes.document] = nodes.document
    translator_type: type[Translator]

    def render(self, doc: nodes.document, /) -> str:
        translator = self.translator_type(doc, self.lw)
        translator.translate()
        return ''.join(translator.body)

class Translator(nodes.DefaultNodeVisitor):

    format = 'unknown'

    def __init__(self, doc: nodes.document, lw: LexWriter, /):
        super().__init__(doc)
        self.head: deque[str] = deque()
        self.body: deque[str] = deque()
        self.foot: deque[str] = deque()
        self.lw = lw

    # def run(self) -> None:
    #     self.doc.emit(self.doc.Event.BeforeTranslate, self)
    #     self.translate()
    #     self.doc.emit(self.doc.Event.AfterTranslate, self)

    def translate(self) -> None:
        self.doc.walkabout(self)

    def get_tagname(self, node: nodes.Node, /) -> str:
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
    escape = staticmethod(html.escape)

    def visit_document(self, node: nodes.document, /):
        raise nodes.SkipDeparture

    def visit_textnode(self, node: nodes.textnode, /):
        self.body.append(self.escape(node))
        raise nodes.SkipDeparture

    def visit_rawtext(self, node: nodes.rawtext, /):
        self.body.append(node)
        raise nodes.SkipDeparture

    def visit_sentence(self, node: nodes.sentence, /):
        rendered = self.lw(node.attributes.pop(NodeKey.sentence))
        if self.lw.charset != self.format:
            rendered = self.escape(rendered)
        self.default_visitor(node)
        self.body.append(rendered)

    def get_attrs_map(self, node: nodes.Element, /) -> dict[str, str]:
        attrs = {}
        todo = dict(node.attributes)
        if todo.get('id'):
            attrs['id'] = str(todo.pop('id'))
        if todo.get('class'):
            todo['classes'].add(str(todo.pop('class')))
        classes = todo.pop('classes')
        if classes:
            attrs['class'] = ' '.join(
                re.sub(r'[\s]+', ' ', c).strip()
                for c in classes)
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

    def default_visitor(self, node: nodes.Node, /):
        self.write_opentag(self.get_tagname(node), self.get_attrs_map(node))

    def default_departer(self, node: nodes.Node, /):
        self.write_closetag(self.get_tagname(node))

@registry.register
class HtmlTabWriter(DoctreeTabWriter):

    __slots__ = EMPTY_SET

    format = 'html'
    translator_type = HtmlTranslator
    jinja = jinja(f'{TEMPLATES_BASE_DIR}/html/static')
    css_template_name = 'tableau.css'
    default_charsets = MapProxy({
        notn: 'html' for notn in Notation})
    defaults = MapProxy(dict(
        wrapper      = True,
        classes      = (),
        wrap_classes = (),
        inline_css   = False))
    _CSS_CACHE = None

    def __call__(self, tab: Tableau, *, classes=None, wrap_classes=None):
        types = self.doc_nodetype.types
        doc = types[nodes.document]()
        if self.opts['wrapper']:
            wrap = types[nodes.wrapper](classes=['tableau-wrapper'])
            wrap['classes'] |= wrap_classes or EMPTY_SET
            wrap['classes'] |= self.opts['wrap_classes']
            doc += wrap
        else:
            wrap = doc
        if self.opts['inline_css']:
            css = '\n' + self.attachments()['css'] + '\n'
            wrap += types[nodes.style](types[nodes.rawtext](css))
        node = types[nodes.tableau].for_object(tab)
        node['classes'] |= classes or EMPTY_SET
        node['classes'] |= self.opts['classes']
        wrap += node
        wrap += types[nodes.clear]()
        return self.render(doc)

    def attachments(self, /):
        css = self.jinja.get_template(self.css_template_name).render()
        return dict(css=css)
        # cls = type(self)
        # cssfile = f'{_staticdir}/{self.css_template_name}'
        # if not cls._CSS_CACHE or cls._CSS_CACHE[0] != cssfile:
        #     with open(cssfile) as f:
        #         cls._CSS_CACHE = cssfile, f.read().replace('<', '&lt;')
        # return dict(css=cls._CSS_CACHE[1])