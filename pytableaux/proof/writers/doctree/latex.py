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
pytableaux.proof.writers.doctree.latex
======================================

"""
from __future__ import annotations

import logging

from ....errors import SkipDeparture
from ....lang import Marking
from ....tools import EMPTY_SET, closure
from . import DoctreeTabWriter, NodeVisitor, Translator


class LatexTranslator(Translator, NodeVisitor):

    format = 'latex'
    logger = logging.getLogger(__name__)

    def setup(self):
        super().setup()
    
    def visit_document(self, node):
        self.head.extend((
            '\\documentclass[10pt]{article}\n',
            '\\usepackage{latexsym, qtree, stmaryrd}\n',
            '\\pagestyle{empty}\n',
            '\\begin{document}\n\n'))

    def depart_document(self, node):
        self.foot.append('\n\n\\end{document}')

    def visit_tableau(self, node):
        self += '\\Tree'
        raise SkipDeparture

    def visit_tree(self, node):
        self += ' [.'

    def depart_tree(self, node):
        self += ' ]'
    
    def visit_node_segment(self, node):
        self += '{'

    def depart_node_segment(self, node):
        self += '}'
    
    def visit_node(self, node):
        if node['data-segment-index'] > 0:
            self += ' \\\\ '
        if 'ticked' in node['classes']:
            self += '\\framebox{'
        self += '$'

    def depart_node(self, node):
        self += '$'
        if 'ticked' in node['classes']:
            self += '}'

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
    
    def visit_subscript(self, node):
        self += '_{'

    def depart_subscript(self, node):
        self += '}'

    def visit_designation(self, node):
        self += self.strings[Marking.tableau, 'designation', node['data-designated']]
        raise SkipDeparture

    def visit_ellipsis(self, node):
        self += '\\vdots{}'
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
    # visit_wrapper = noop

    @staticmethod
    def escape(s: str, /):
        return escape_latex(s)

class LatexTabWriter(DoctreeTabWriter):

    __slots__ = EMPTY_SET

    format = 'latex'
    file_extension = 'tex'
    translator_type = LatexTranslator

    def build_doc(self, tab, /):
        return super().build_doc(tab)

@closure
def escape_latex():
    # Table copied from sphinx.util.texescape.
    # https://github.com/sphinx-doc/sphinx/blob/a7f5d91/sphinx/util/texescape.py
    # Copyright (c) 2007-2023 by the Sphinx team.
    # BSD-2 License. See NOTICE file for details.
    trans = dict((ord(key), value) for key, value in (
        # map TeX special chars
        ('$', r'\$'),
        ('%', r'\%'),
        ('&', r'\&'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('\\', r'\textbackslash{}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
        # map chars to avoid mis-interpretation in LaTeX
        ('[', r'{[}'),
        (']', r'{]}'),
        # map special Unicode characters to TeX commands
        ('✓', r'\(\checkmark\)'),
        ('✔', r'\(\pmb{\checkmark}\)'),
        ('✕', r'\(\times\)'),
        ('✖', r'\(\pmb{\times}\)'),
        # used to separate -- in options
        ('﻿', r'{}'),
        # map some special Unicode characters to similar ASCII ones
        # (even for Unicode LaTeX as may not be supported by OpenType font)
        ('⎽', r'\_'),
        ('ℯ', r'e'),
        ('ⅈ', r'i')))
    
    def escape(s: str):
        return s.translate(trans)
    return escape