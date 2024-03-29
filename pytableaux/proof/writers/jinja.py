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
pytableaux.proof.writers.jinja
==============================

"""
from __future__ import annotations

import os
from collections import deque
from typing import Sequence

import jinja2

from ..tableaux import Tableau
from . import TabWriter, TabWriterRegistry

__all__ = (
    'JinjaTabWriter',
    'registry',
    'TextTabWriter')

NOARG = object()

TEMPLATES_BASE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'templates')

def jinja(searchpath, *, trim_blocks=True, lstrip_blocks=True, **opts):
    return jinja2.Environment(
        trim_blocks=trim_blocks,
        lstrip_blocks=lstrip_blocks,
        loader=jinja2.FileSystemLoader(searchpath),
        **opts)

class JinjaTabWriter(TabWriter):

    engine = 'jinja'
    template_searchpath: str|Sequence[str]
    template_name: str
    jinja: jinja2.Environment

    def __call__(self, tab: Tableau, **kw):
        return self.render(self.template_name, tab=tab, **kw)
    
    def render(self, template: str, *args, **kw) -> str:
        return self.get_template(template).render(*args, **kw)

    def get_template(self, name: str, *args, **kw):
        context = dict(lw=self.lw, opts=self.opts)
        context.update(*args, **kw)
        return self.jinja.get_template(name, None, context)

registry = TabWriterRegistry(name=JinjaTabWriter.engine)

@registry.register(default=True)
class TextTabWriter(JinjaTabWriter):
    """Plain text tableau writer."""

    format = 'text'
    file_extension = 'txt'
    template_name = 'nodes.jinja2'
    jinja = jinja(f'{TEMPLATES_BASE_DIR}/{format}')

    def __call__(self, tab: Tableau) -> str:
        template = self.get_template(self.template_name)
        return self._write_structure(tab.tree, template)

    def _write_structure(self, s: Tableau.Tree, template: jinja2.Template, *, prefix = ''):
        nodestr = template.render(structure = s)
        lines = deque()
        lines.append(prefix + nodestr)
        prefix += ' ' * (len(nodestr) - 1)
        for c, child in enumerate(s.children):
            is_last = c == len(s.children) - 1
            next_pfx = prefix + (' ' if is_last else '|')
            lines.append(self._write_structure(child, template, prefix=next_pfx))
            if not is_last:
                lines.append(next_pfx)
        return '\n'.join(lines)
