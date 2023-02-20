# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
from typing import TYPE_CHECKING, Mapping

import jinja2

from .. import __docformat__
from ..errors import Emsg, check
from ..lang import LexWriter, Notation
from ..tools import EMPTY_MAP, abcs, closure, qset

if TYPE_CHECKING:
    from . import Tableau, TreeStruct

__all__ = (
    'HtmlTabWriter',
    'TabWriter',
    'TemplateTabWriter',
    'TextTabWriter',
    'registry',
    'register')

registry: Mapping
"""The tableau writer class registry.

:meta hide-value:
"""

@closure
def register():

    global registry

    regtable = {}
    registry = MapProxy(regtable)

    def register(wcls,/, *, force: bool = False):
        """Register a ``TabWriter`` class. Returns the argument, so it can be
        used as a decorator.

        Args:
            wcls: The writer class.
        
        Returns:
            The writer class.
        """
        wcls = check.subcls(wcls, TabWriter)
        if abcs.isabstract(wcls):
            raise TypeError(f'Cannot register abstract class: {wcls}')
        fmt = wcls.format
        if not force and fmt in registry:
            raise KeyError(f"Format {fmt} already registered")
        regtable[fmt] = wcls
        return wcls

    return register

class TabWriterMeta(abcs.AbcMeta):

    DefaultFormat = 'text'

    def __call__(cls, *args, **kw):
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
    def write(self, tableau, /, **kw) -> str:
        raise NotImplementedError

    __call__ = write

    def __init_subclass__(subcls, **kw):
        super().__init_subclass__(**kw)
        subcls.__call__ = subcls.write

_templates_base_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'templates')

class TemplateTabWriter(TabWriter):

    template_dir: str

    jinja_opts = MapProxy(dict(
        trim_blocks   = True,
        lstrip_blocks = True))
    _jenv:jinja2.Environment

    @classmethod
    def render(cls, template: str, *args, **kw) -> str:
        return cls._jenv.get_template(template).render(*args, **kw)

    def __init_subclass__(subcls, **kw):
        super().__init_subclass__(**kw)
        if abcs.isabstract(subcls):
            return
        if getattr(subcls, '_jenv', None) is None:
            if 'loader' not in subcls.jinja_opts:
                jopts = dict(subcls.jinja_opts)
                if getattr(subcls, 'template_dir', None) is None:
                    subcls.template_dir = os.path.join(_templates_base_dir, subcls.format)
                jopts['loader'] = jinja2.FileSystemLoader(subcls.template_dir)
            subcls._jenv = jinja2.Environment(**jopts)

@register
class HtmlTabWriter(TemplateTabWriter):
    """HTML tableau writer.
    """

    format = 'html'

    default_charsets = {notn: 'html' for notn in Notation}

    defaults = MapProxy(dict(
        wrapper      = True,
        classes      = (),
        wrap_classes = (),
        inline_css   = False))

    def write(self, tab, /, *, classes = None) -> str:
        """"
        Args:
            tab: The tableaux instance.
            classes: Additional classes for the main tableau element. Merged
                with `classes` option.
        """
        opts = self.opts
        wrap_classes = qset(opts['wrap_classes'])
        wrap_classes.add('tableau-wrapper')
        tab_classes = qset(opts['classes'])
        tab_classes.add('tableau')
        if classes is not None:
            tab_classes.extend(classes)
        return self.render('tableau.jinja2',
            tab = tab,
            lw = self.lw,
            opts = opts,
            wrap_classes = wrap_classes,
            tab_classes = tab_classes)

    def attachments(self, /) -> dict[str, str]:
        """
        Returns:
            A dict with:
              - `css`: The static css.
        """
        return dict(
            css = self.render('static/tableau.css'))

    # classes:
    #   wrapper : tableau-wrapper
    #   tableau : tableau
    #   structure : structure [, root, has-open, has-closed, leaf, only-branch, closed, open]
    #   node segment : node-sement
    #   vertical line : vertical-line
    #   horizontal line : horizontal-line
    #   node : node [, ticked]
    #   node props : node-props [, ticked]
    #   inline : [sentence, world, designation, designated, undesignated,
    #             world1, world2, access, ellipsis, flag, <flag>]
    #   misc : clear

@register
class TextTabWriter(TemplateTabWriter):
    """Plain text tableau writer."""

    format = 'text'

    defaults = MapProxy(dict(
        # summary  = False,
        # argument = False,
        # title    = False,
    ))
    """Default options."""

    def write(self, tab: Tableau, /) -> str:
        strs = deque()
        # opts = self.opts
        # if opts['title']:
        #     strs.append(self._write_title(tab))
        # if opts['summary']:
        #     strs.append(self._write_summary(tab))
        # if tab.argument and opts['argument']:
        #     strs.append(self._write_argument(tab.argument))
        template = self._jenv.get_template('nodes.jinja2', None, dict(lw = self.lw))
        strs.append(self._write_structure(tab.tree, template))
        return '\n'.join(strs)

    def _write_structure(self, s: TreeStruct, template: jinja2.Template, *, prefix = '',):
        nodestr = template.render(structure = s)
        lines = deque()
        append = lines.append
        writestruct = self._write_structure
        append(prefix + nodestr)
        children = s.children
        prefix += ' ' * (len(nodestr) - 1)
        for c, child in enumerate(children):
            is_last = c == len(children) - 1
            next_pfx = prefix + (' ' if is_last else '|')
            append(writestruct(child, template, prefix = next_pfx))
            if not is_last:
                append(next_pfx)
        return '\n'.join(lines)

    # def _write_title(self, tab: Tableau, /) -> str:
    #     return self.render('title.jinja2', logic = tab.logic)

    # def _write_argument(self, arg: Argument, /) -> str:
    #     lw = self.lw
    #     return self.render('argument.jinja2', 
    #         premises = tuple(map(lw, arg.premises)),
    #         conclusion = lw(arg.conclusion),
    #     )

    # def _write_summary(self, tab: Tableau, /) -> str:
    #     return self.render('summary.jinja2', tab = tab)

    # def _get_argstrs(self, arg: Argument|None, /) -> dict[str, tuple[str, ...]|str|None]:
    #     if arg is None:
    #         return dict(premises = None, conclusion = None)
    #     return dict(
    #         premises = tuple(map(lw := self.lw, arg.premises)),
    #         conclusion = lw(arg.conclusion),
    #     )
