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
pytableaux.proof.writers.doctree.html
=====================================

"""
from __future__ import annotations

import html
import logging
import re
from collections import deque
from types import MappingProxyType as MapProxy
from typing import Any, Mapping, Sequence

from ....errors import SkipDeparture
from ....lang import Notation
from ....tools import EMPTY_SET, inflect
from ...tableaux import Tableau
from ..jinja import TEMPLATES_BASE_DIR, jinja
from . import DefaultNodeVisitor, DoctreeTabWriter, Translator, nodes

__all__ = (
    'HtmlTabWriter',
    'HtmlTranslator')

class HtmlTranslator(Translator, DefaultNodeVisitor):

    format = 'html'
    logger = logging.getLogger(__name__)
    escape = staticmethod(html.escape)

    def default_visitor(self, node):
        if isinstance(node, nodes.BlockElement):
            self.body.append('\n')
        self.body.append(
            self.get_opentag(
                self.get_tagname(node),
                self.get_attrs_map(node)))

    def default_departer(self, node):
        self.body.append(
            self.get_closetag(self.get_tagname(node)))

    def visit_document(self, node):
        self.head.append('\n'.join((
            '<!DOCTYPE html>',
            self.get_opentag('html', dict(lang='en')),
            self.get_opentag('body', None))))
        self.head.append('\n')

    def depart_document(self, node):
        if self.body:
            self.foot.append('\n')
        self.foot.append('\n'.join((
            self.get_closetag('body'),
            self.get_closetag('html'))))

    def visit_textnode(self, node):
        self.body.append(self.escape(node))
        raise SkipDeparture

    def visit_rawtext(self, node):
        self.body.append(node)
        raise SkipDeparture

    def visit_sentence(self, node: nodes.Element):
        rendered = self.lw(node.attributes.pop('data-sentence'))
        if self.lw.charset != self.format:
            rendered = self.escape(rendered)
        self.default_visitor(node)
        self.body.append(rendered)

    def visit_world(self, node):
        self.default_visitor(node)
        self.body.append('w')

    def visit_access(self, node):
        self.default_visitor(node)
        self.body.append(self.access_marker)

    def visit_designation(self, node):
        self.default_visitor(node)
        marker = self.designation_markers[node['data-designated']]
        self.body.append(marker)

    def visit_flag(self, node):
        self.default_visitor(node)
        flag = node['data-flag']
        if flag in self.flag_markers:
            self.body.append(self.flag_markers[flag])

    def visit_ellipsis(self, node):
        self.default_visitor(node)
        self.body.append('&vellip;')

    def visit_separator(self, node):
        self.default_visitor(node)
        if 'sentence-world' in node['classes']:
            sep = ', '
        else:
            sep = ' '
        self.body.append(sep)

    def get_opentag(self, tagname: str, attrs: Mapping[str, Any]|None) -> str:
        parts = deque()
        parts.append('<')
        parts.append(self.escape(tagname))
        if attrs:
            parts.append(' ')
            parts.append(self.get_attrs_str(attrs))
        parts.append('>')
        return ''.join(parts)

    def get_closetag(self, tagname: str) -> str:
        return f'</{self.escape(tagname)}>'

    def get_tagname(self, node: nodes.Node, /) -> str:
        try:
            tagname = node.tagnames[self.format]
        except KeyError:
            tagname = node.tagname
        if tagname:
            return tagname
        raise ValueError(f'tagname: {tagname}')

    def get_attrs_str(self, attrs: Mapping[str, str]) -> str:
        return ' '.join(
            '='.join((self.escape(k), f'"{self.escape(v)}"'))
            for k, v in attrs.items())

    def get_attrs_map(self, node: nodes.Element) -> dict[str, str]:
        attrs = {}
        todo = dict(node.attributes)
        if todo.get('id'):
            attrs['id'] = str(todo.pop('id'))
        for key in sorted(todo):
            value = todo.pop(key)
            if key == 'class':
                todo['classes'] |= re.split(r'\s+', value)
                continue
            if value is None:
                value = ''
            elif isinstance(value, bool):
                value = '1' if value else ''
            elif isinstance(value, (int, float)):
                value = str(value)
            name = key.replace('_', '-')
            if name == 'classes':
                name = 'class'
            if isinstance(value, str):
                attrs[name] = value
                continue
            if isinstance(value, Sequence):
                if name == 'class':
                    attrs[name] = ' '.join(
                        re.sub(r'\s+', ' ', value).strip()
                        for value in value)
                    continue
            if isinstance(value, Mapping):
                if name == 'style':
                    attrs[name] = ' '.join(
                        f"{inflect.dashcase(key)}: {value};"
                        for key, value in value.items())
                    continue
            self.logger.warning(
                f'Skipping {key} attribute of type {type(value)}')
        return attrs

class HtmlTabWriter(DoctreeTabWriter):

    __slots__ = EMPTY_SET

    format = 'html'
    translator_type = HtmlTranslator
    jinja = jinja(f'{TEMPLATES_BASE_DIR}/html/static')
    css_template_name = 'tableau.css'
    default_charsets = MapProxy({
        notn: 'html' for notn in Notation})
    defaults = MapProxy(dict(DoctreeTabWriter.defaults,
        wrapper      = True,
        classes      = (),
        wrap_classes = (),
        inline_css   = False))

    def build_doc(self, tab: Tableau, *, classes=None, wrap_classes=None):
        types = self.docnode_type.types
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
        return doc
    
    def attachments(self):
        css = self.jinja.get_template(self.css_template_name).render()
        return dict(css=css)