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
from types import MappingProxyType as MapProxy
from typing import Sequence

import jinja2

from ... import __docformat__
from ...lang import Notation
from ...tools import EMPTY_SET, abcs, qset
from ..tableaux import Tableau
from . import TabWriter, TabWriterRegistry

__all__ = (
    'HtmlTabWriter',
    'JinjaTabWriter',
    'registry',
    'TextTabWriter')

NOARG = object()

registry = TabWriterRegistry()

_templates_base_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'templates')

class JinjaTabWriter(TabWriter):

    template_searchpath: str|Sequence[str]
    template_name: str
    jinja_env: jinja2.Environment
    jinja_opts = MapProxy(dict(
        trim_blocks   = True,
        lstrip_blocks = True))

    def __call__(self, tab: Tableau, **kw):
        return self.render(self.template_name, tab=tab, **kw)
    
    def render(self, template: str, *args, **kw) -> str:
        return self.get_template(template).render(*args, **kw)

    def get_template(self, name: str, *args, **kw):
        context = dict(lw=self.lw, opts=self.opts)
        context.update(*args, **kw)
        return self.jinja_env.get_template(name, None, context)

    @classmethod
    def jinja_init(cls):
        cls.jinja_env = jinja2.Environment(**dict(cls.jinja_opts,
            loader=jinja2.FileSystemLoader(cls.template_searchpath)))

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        if not abcs.isabstract(cls):
            cls.jinja_init()

@registry.register
class HtmlTabWriter(JinjaTabWriter):
    """HTML tableau writer.
    """

    format = 'html'
    template_searchpath = f'{_templates_base_dir}/html'
    template_name = 'tableau.jinja2'
    css_template_name = 'static/tableau.css'
    default_charsets = {notn: 'html' for notn in Notation}
    defaults = MapProxy(dict(
        wrapper      = True,
        classes      = (),
        wrap_classes = (),
        inline_css   = False))

    def __call__(self, tab: Tableau, *, classes = None, wrap_classes = None) -> str:
        """"
        Args:
            tab: The tableaux instance.
            classes: Additional classes for the main tableau element. Merged
                with `classes` option.
        """
        tab_classes = qset(classes or EMPTY_SET)
        tab_classes.update(self.opts['classes'])
        tab_classes.add('tableau')
        wrap_classes = qset(wrap_classes or EMPTY_SET)
        wrap_classes.update(self.opts['wrap_classes'])
        wrap_classes.add('tableau-wrapper')
        return super().__call__(tab,
            wrap_classes = wrap_classes,
            tab_classes = tab_classes,
            css_template_name = self.css_template_name)

    def attachments(self, /) -> dict[str, str]:
        """
        Returns:
            A dict with:
              - `css`: The static css.
        """
        return dict(css=self.render(self.css_template_name))

@registry.register
class TextTabWriter(JinjaTabWriter):
    """Plain text tableau writer."""

    format = 'text'
    template_searchpath = f'{_templates_base_dir}/text'
    template_name = 'nodes.jinja2'

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