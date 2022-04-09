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
#
# ------------------
#
# pytableaux - tableau writers module
from __future__ import annotations

__all__ = (
    'TabWriter',
)

from errors import Emsg
from lexicals import Argument, LexWriter, Notation
from proof.tableaux import Tableau, TreeStruct
from tools.abcs import abstract, overload, abcf, abcm, AbcMeta, MapProxy, TT

import jinja2
import os
from typing import Any, ClassVar, Collection, Mapping

class TabWriterMeta(AbcMeta):
    def __call__(cls, *args, **kw):
        if cls is TabWriter:
            if args:
                fmt, *args = args
            else:
                fmt = TabWriter.DefaultFormat
            return TabWriter.Registry[fmt](*args, **kw)
        return super().__call__(*args, **kw)

class TabWriter(metaclass = TabWriterMeta):

    Registry: ClassVar[Mapping[str, type[TabWriter]]]
    DefaultFormat = 'text'

    #: The format registry identifier.
    format: ClassVar[str]
    #: Default LexWriter charset for each notation.
    default_charsets: ClassVar[Mapping[Notation, str]] = MapProxy({
        notn: notn.default_charset for notn in Notation
    })
    #: Default options.
    defaults: Mapping[str, Any] = MapProxy()

    lw: LexWriter
    opts: dict[str, Any]

    def __init__(self, notn: Notation|str = None, charset: str = None, *, lw: LexWriter = None, **opts):
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
                if Notation(notn) != lw.notation:
                    raise Emsg.ValueConflict(notn, lw.notation)
            if charset is not None:
                if charset != lw.charset:
                    raise Emsg.ValueConflict(charset, lw.charset)
        self.lw = lw
        self.opts = dict(self.defaults) | opts

    def attachments(self, /) -> Mapping[str, Any]:
        return {}

    @abstract
    def write(self, tableau: Tableau, /, **kw) -> str:
        raise NotImplementedError

    __call__ = write

    def __init_subclass__(subcls: type[TemplateWriter], **kw):
        super().__init_subclass__(**kw)
        subcls.__call__ = subcls.write

    @classmethod
    @overload
    def register(cls, subcls: TT) -> TT: ...

    @abcf.before
    def prepare(ns: dict, bases):

        _registry: dict[str, type[TabWriter]] = {}

        def register(cls: type[TabWriter], subcls: type[TabWriter]):
            'Update available writers.'
            if not issubclass(subcls, __class__):
                raise TypeError(subcls, __class__)
            if abcm.isabstract(subcls):
                raise TypeError('Cannot register abstract class: %s' % subcls)
            fmt = subcls.format
            if fmt in _registry:
                raise TypeError(
                    "%s format '%s' already registered" % (__class__.__name__, fmt)
                )
            _registry[fmt] = subcls
            type(cls).register(cls, subcls)
            return subcls

        ns.update(
            Registry = MapProxy(_registry),
            register = classmethod(register),
        )

_templates_base_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'templates'
)

class TemplateWriter(TabWriter):

    template_dir: ClassVar[str]
    main_template: ClassVar[str]
    _jenv: ClassVar[jinja2.Environment]
    _jinja_opts: ClassVar[Mapping[str, Any]] = MapProxy(dict(
        trim_blocks   = True,
        lstrip_blocks = True,
    ))

    def _render(self, template: str, *args, **kw) -> str:
        return self._jenv.get_template(template).render(*args, **kw)

    def __init_subclass__(subcls: type[TemplateWriter], **kw):
        super().__init_subclass__(**kw)
        if abcm.isabstract(subcls):
            return
        if getattr(subcls, '_jenv', None) is None:
            if 'loader' not in subcls._jinja_opts:
                jopts = dict(subcls._jinja_opts)
                if getattr(subcls, 'template_dir', None) is None:
                    subcls.template_dir = os.path.join(_templates_base_dir, subcls.format)
                jopts['loader'] = jinja2.FileSystemLoader(subcls.template_dir)
            subcls._jenv = jinja2.Environment(**jopts)

@TabWriter.register
class HtmlTabWriter(TemplateWriter):

    format = 'html'
    default_charsets = {notn: 'html' for notn in Notation}
    defaults = dict(
        classes      = (),
        wrap_classes = (),
        inline_css   = False,
    )

    def write(self, tab: Tableau, /, classes: Collection[str] = None):
        opts = self.opts
        wrap_classes = ['tableau-wrapper']
        wrap_classes.extend(opts['wrap_classes'])
        tab_classes = ['tableau']
        tab_classes.extend(opts['classes'])
        if classes is not None:
            tab_classes.extend(classes)
        return self._render('tableau.jinja2',
            tab = tab,
            lw = self.lw,
            opts = opts,
            wrap_classes = wrap_classes,
            tab_classes = tab_classes,
        )

    def attachments(self, /):
        return dict(
            css = self._render('static/tableau.css')
        )

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

@TabWriter.register
class TextTabWriter(TemplateWriter):

    format = 'text'
    defaults = dict(
        summary  = True,
        argument = True,
        heading  = True,
    )

    def write(self, tab: Tableau, /):
        strs = []
        opts = self.opts
        if opts['summary']:
            premises, conclusion = self._get_argstrs(tab.argument)
            strs.append(self._render('summary.jinja2',
                stats      = tab.stats,
                logic      = tab.logic,
                argument   = tab.argument,
                premises   = premises,
                conclusion = conclusion,
            ))
        if opts['heading']:
            strs.append(self._render('heading.jinja2',
                logic = tab.logic,
            ))
        template = self._jenv.get_template('nodes.jinja2')
        strs.append(self._write_structure(tab.tree, template))
        return '\n'.join(strs)

    def _write_structure(self, structure: TreeStruct, template: jinja2.Template, *, prefix: str = '',):
        nodestr = template.render(structure = structure, lw = self.lw)
        lines = [prefix + nodestr]
        children = structure.children
        prefix += (' ' * (len(nodestr) - 1))
        for c, child in enumerate(children):
            is_last = c == len(children) - 1
            next_pfx = prefix + (' ' if is_last else '|')
            lines.append(self._write_structure(child, template, prefix = next_pfx))
            if not is_last:
                lines.append(next_pfx)
        return '\n'.join(lines)

    def _get_argstrs(self, arg: Argument, /) -> tuple[tuple[str, ...], str]:
        if not arg:
            return (None, None)
        lw = self.lw
        return tuple(map(lw, arg.premises)), lw(arg.conclusion)