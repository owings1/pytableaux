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
pytableaux.proof.writers.doctree.text
=====================================

WIP
"""
from __future__ import annotations

import logging
from typing import Any, Self

from ....errors import SkipDeparture
from ....lang import Marking
from ....tools import EMPTY_SET
from . import DoctreeTabWriter, NodeVisitor, Translator


class TextTranslator(Translator, NodeVisitor):

    format = 'text'
    logger = logging.getLogger(__name__)

    def setup(self):
        super().setup()
        self.prefix = ''
        self.nodestr = ''
        self.nodecontext = False
    
    def visit_document(self, node):
        raise SkipDeparture

    def visit_tableau(self, node):
        raise SkipDeparture

    def visit_tree(self, node):
        raise SkipDeparture

    def visit_node_segment(self, node):
        self.nodestr = ''
        self.nodecontext = True
        if len(self.body):
            self += '-- '

    def depart_node_segment(self, node):
        if len(self.body):
            self.body.append('\n')
        self.body.append(self.prefix + self.nodestr)
        self.prefix += ' ' * (len(self.nodestr) - 1)
        self.nodecontext = False
    
    def visit_node(self, node):
        pass

    def depart_node(self, node):
        if 'ticked' in node['classes']:
            self += ' *'
        nodetype = node['data-node-type']
        if 'Closure' not in nodetype and 'Flag' not in nodetype:
            self += '; '

    def visit_sentence(self, node):
        rendered = self.lw(node['data-sentence'])
        if self.lw.format != self.format:
            rendered = self.escape(rendered)
        self += rendered
        raise SkipDeparture

    def visit_separator(self, node):
        if 'sentence-world' in node['classes']:
            sep = ', '
        else:
            sep = ' '
        self += sep
        raise SkipDeparture

    def visit_world(self, node):
        self += 'w'
        raise SkipDeparture

    def visit_access(self, node):
        self += self.strings[Marking.tableau, 'access']
        raise SkipDeparture

    def visit_textnode(self, node):
        self += self.escape(node)
        raise SkipDeparture
    
    def visit_designation(self, node):
        self += self.strings[Marking.tableau, 'designation', node['data-designated']]
        raise SkipDeparture

    def visit_ellipsis(self, node):
        self += '...'
        raise SkipDeparture

    def visit_flag(self, node):
        flag = node['data-flag']
        try:
            marker = self.strings[Marking.tableau, 'flag', flag]
        except KeyError:
            marker = self.escape(flag)
        self += marker
        raise SkipDeparture

    def visit_clear(self, node):
        self += '\n\n'
        raise SkipDeparture

    def noop(self, node):
        raise SkipDeparture

    visit_horizontal_line = noop
    visit_vertical_line = noop
    visit_node_props = noop
    visit_child_wrapper = noop
    visit_subscript = noop
    # visit_wrapper = noop

    @staticmethod
    def escape(s: str, /):
        return s

    def __iadd__(self, item: Any) -> Self:
        if not self.nodecontext:
            return super().__iadd__(item)
        if isinstance(item, str):
            self.nodestr += item
        else:
            self.nodestr += ''.join(item)
        return self


class TextTabWriter(DoctreeTabWriter):

    __slots__ = EMPTY_SET

    format = 'text'
    translator_type = TextTranslator

    def build_doc(self, tab, /):
        return super().build_doc(tab)
