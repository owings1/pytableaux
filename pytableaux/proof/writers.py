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
pytableaux.proof.writers
========================

"""
from __future__ import annotations

import os
from abc import abstractmethod as abstract
from collections import deque
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Mapping, Self, TypeVar

from .. import __docformat__
from ..errors import Emsg, check
from ..lang import LexWriter, Notation
from ..tools import EMPTY_MAP, abcs, closure, qset

_T = TypeVar('_T')
_TWT = TypeVar('_TWT', bound='TabWriter')

if TYPE_CHECKING:
    from . import Tableau, TreeStruct
    import jinja2

__all__ = (
    'HtmlTabWriter',
    'TabWriter',
    'TemplateTabWriter',
    'TextTabWriter',
    'registry',
    'register')

_templates_base_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'templates')

registry: Mapping[str, type[TabWriter]]
"""The tableau writer class registry.

:meta hide-value:
"""

@closure
def register():

    global registry

    regtable = {}
    registry = MapProxy(regtable)

    def register(cls: type[_TWT], /, *, force: bool = False) -> type[_TWT]:
        """Register a ``TabWriter`` class. Returns the argument, so it can be
        used as a decorator.

        Args:
            wcls: The writer class.
        
        Returns:
            The writer class.
        """
        cls = check.subcls(cls, TabWriter)
        if abcs.isabstract(cls):
            raise TypeError(f'Cannot register abstract class: {cls}')
        fmt = cls.format
        if not force and fmt in registry:
            raise KeyError(f"Format {fmt} already registered")
        regtable[fmt] = cls
        return cls

    return register

class TabWriterMeta(abcs.AbcMeta):

    DefaultFormat = 'text'

    def __call__(cls: type[_T]|Self, *args, **kw) -> _T:
        if cls is TabWriter:
            if args:
                fmt, *args = args
            else:
                fmt = cls.DefaultFormat
            return registry[fmt](*args, **kw)
        return super().__call__(*args, **kw)

class TabWriter(metaclass = TabWriterMeta):
    """Tableau writer base class.

    Constructing a ``TabWriter``.

    Examples::

        # make an instance of the default writer class, with the default notation.
        writer = TabWriter()

        # make an HtmlTabWriter, with the default notation and charset.
        writer = TabWriter('html')

        # make an HtmlTabWriter, with standard notation and ASCII charset.
        writer = TabWriter('html', 'standard', 'ascii')
    """

    format: str
    "The format registry identifier."

    default_charsets = MapProxy({
        notn: notn.default_charset for notn in Notation})
    "Default ``LexWriter`` charset for each notation."

    defaults = EMPTY_MAP
    "Default options."

    lw: LexWriter
    "The writer's `LexWriter` instance."

    opts: dict
    "The writer's options."

    def __init__(self, notn = None, charset = None, *, lw: LexWriter = None, **opts):
        if lw is None:
            if notn is None:
                notn = Notation.default
            else:
                notn = Notation(notn)
            if charset is None:
                charset = self.default_charsets[notn]
            lw = LexWriter(notn, charset, **opts)
        else:
            if notn is not None:
                if Notation(notn) is not lw.notation:
                    raise Emsg.ValueConflict(notn, lw.notation)
            if charset is not None:
                if charset != lw.charset:
                    raise Emsg.ValueConflict(charset, lw.charset)
        self.lw = lw
        self.opts = dict(self.defaults) | opts

    def attachments(self, /):
        return EMPTY_MAP

    @abstract
    def write(self, tab: Tableau, **kw) -> str:
        raise NotImplementedError

    __call__ = write

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        cls.__call__ = cls.write

class JinjaTabWriter(TabWriter):

    template_searchpath: str
    template_name: str

    jinja_opts = MapProxy(dict(
        trim_blocks   = True,
        lstrip_blocks = True))
    jinja_env: jinja2.Environment

    def write(self, tab: Tableau, **kw):
        return self.render(self.template_name, tab=tab, **kw)
    
    def render(self, template: str, *args, **kw) -> str:
        return self.get_template(template).render(*args, **kw)

    def get_template(self, name: str, *args, **kw):
        context = dict(lw=self.lw, opts=self.opts)
        context.update(*args, **kw)
        return self.jinja_env.get_template(name, None, context)

    @classmethod
    def jinja_init(cls):
        import jinja2
        cls.jinja_env = jinja2.Environment(**dict(cls.jinja_opts,
            loader=jinja2.FileSystemLoader(cls.template_searchpath)))

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        if not abcs.isabstract(cls):
            cls.jinja_init()

@register
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

    def write(self, tab: Tableau, *, classes = None) -> str:
        """"
        Args:
            tab: The tableaux instance.
            classes: Additional classes for the main tableau element. Merged
                with `classes` option.
        """
        wrap_classes = qset(self.opts['wrap_classes'])
        wrap_classes.add('tableau-wrapper')
        tab_classes = qset(self.opts['classes'])
        tab_classes.add('tableau')
        if classes is not None:
            tab_classes.extend(classes)
        return super().write(tab,
            wrap_classes = wrap_classes,
            tab_classes = tab_classes)

    def attachments(self, /) -> dict[str, str]:
        """
        Returns:
            A dict with:
              - `css`: The static css.
        """
        return dict(css=self.render(self.css_template_name))


@register
class TextTabWriter(JinjaTabWriter):
    """Plain text tableau writer."""

    format = 'text'
    template_searchpath = f'{_templates_base_dir}/text'
    template_name = 'nodes.jinja2'

    def write(self, tab: Tableau) -> str:
        template = self.get_template(self.template_name)
        return self._write_structure(tab.tree, template)

    def _write_structure(self, s: TreeStruct, template: jinja2.Template, *, prefix = ''):
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
