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
#
# ------------------
"""
pytabdoc.nodez
^^^^^^^^^^^^^^
"""
from __future__ import annotations

import html
import itertools
from typing import TYPE_CHECKING, NamedTuple

import docutils.writers._html_base
import sphinx.addnodes
import sphinx.writers.html5
from docutils import nodes
from docutils.nodes import Element
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.writers.html5 import HTML5Translator as BaseTranslator

from pytableaux.lang import LexWriter, Notation

from . import ConfKey

if TYPE_CHECKING:

    class BaseTranslator(sphinx.writers.html5.HTML5Translator, docutils.writers._html_base.HTMLTranslator, nodes.NodeVisitor):
        # body: list[str]
        document: sphinx.addnodes.document

__all__ = (
    'sentence',
    'block',
    'HTML5Translator')

logger = logging.getLogger(__name__)


class HTML5Translator(BaseTranslator):

    class OptStacks(NamedTuple):
        notn: list
        format: list

    def __init__(self, document, builder):
        super().__init__(document, builder)
        self.optstacks = self.OptStacks([], [])

    def visit_block(self, node):
        self.body.append(self.starttag(node, 'div', ''))

    def depart_block(self, node):
        self.body.append('</div>\n')

    def visit_sentence(self, node: Element):
        self.body.append(self.starttag(node, 'span', '', CLASS = 'sentence'))
        notn, fmt = self.get_lwargs(node)
        if node.get('rendered'):
            return
        if (s := node.get('sentence')):
            lw = LexWriter(notn, fmt)
            try:
                content = lw(s)
                node['rendered'] = content
                node['escaped'] = content
                if lw.format != 'html':
                    content = html.escape(content)
                    node['escaped'] = content
            except:
                logger.error(f'Failed to render sentence {s} for node: {node}, '
                    f' {self.document["source"]}')
                raise
            self.body.append(content)

    def depart_sentence(self, node):
        self.body.append('</span>')
        for stack in self.optstacks:
            if stack and stack[-1][0] is node:
                stack.pop()

    def starttag(self, node, tagname, suffix='\n', empty=False, **attributes):
        for name, value in getattr(node, 'attributes', {}).items():
            if name.startswith('data-'):
                attributes[name] = value
        return super().starttag(node, tagname, suffix, empty, **attributes)

    def get_lwargs(self, node: Element):
        stacks = self.optstacks
        if (notn := node.get('notn')):
            stacks.notn.append((node, Notation(notn)))
        else:
            if stacks.notn:
                notn = stacks.notn[-1][1]
            else:
                notn = self.config[ConfKey.wnotn]
        if (format := node.get('format')):
            stacks.format.append((node, format))
        else:
            if stacks.format:
                format = stacks.format[-1][1]
            else:
                format = self.builder.format
        return notn, format


class sentence(nodes.Inline, nodes.TextElement): pass
class block(nodes.Element): pass


def _noop(self, node): pass

def __visit_inline(self, node):
    self.visit_inline(node)

def __depart_inline(self, node):
    self.depart_inline(node)

def setup(app: Sphinx):

    translators = app.registry.translators

    if (base := translators.get('html')) and not issubclass(HTML5Translator, base):
        raise TypeError(f'Class conflict with {HTML5Translator} and {base}')

    app.set_translator('html', HTML5Translator, True)

    formats = {'text', 'latex', 'man', 'texinfo'}
    formats.update(translators)
    formats.discard('html')
    noops =   dict(zip(formats, itertools.repeat((_noop, _noop))))
    inlines = dict(zip(formats, itertools.repeat((__visit_inline, __depart_inline))))
    
    app.add_node(block, **noops)
    app.add_node(sentence, **inlines)

