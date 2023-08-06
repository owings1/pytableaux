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
from abc import abstractmethod
from collections import deque
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Callable, MutableMapping, Self, Sequence, TypeVar

from .. import __docformat__
from ..errors import Emsg, check
from ..lang import LexWriter, Notation
from ..tools import EMPTY_MAP, EMPTY_SET, abcs, qset, MapCover

NOARG = object()
_T = TypeVar('_T')
_TWT = TypeVar('_TWT', bound='TabWriter')

if TYPE_CHECKING:
    from typing import overload
    from . import Node, Tableau, TreeStruct
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

    __slots__ = ('lw', 'opts')

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

    @abstractmethod
    def __call__(self, tab: Tableau, **kw) -> str:
        raise NotImplementedError


class Registry(MapCover[str, type[TabWriter]], MutableMapping[str, type[TabWriter]]):
    "A tableau writer class registry."

    __slots__ = ('register', '__delitem__')

    def __init__(self):
        super().__init__(mapping := {})
        def register(cls=NOARG, /, *, key=None, force=False):
            if cls is NOARG:
                return lambda cls: register(cls, key=key, force=force)
            cls = check.subcls(cls, TabWriter)
            if abcs.isabstract(cls):
                raise TypeError(f'Cannot register abstract class: {cls}')
            if key is None:
                key = cls.format
            if not force and key in self:
                raise KeyError(f"Format/key {key} already registered")
            mapping[check.inst(key, str)] = cls
            return cls
        def delitem(key):
            del mapping[key]
        self.register = register
        self.__delitem__ = delitem

    def __setitem__(self, key, value):
        self.register(value, key=key, force=True)

    if TYPE_CHECKING:
        @overload
        def register(self, cls: type[_TWT], /, *, key: str = ..., force: bool = ...) -> type[_TWT]:
            """Register a ``TabWriter`` class. Returns the argument, so it can be
            used as a decorator.

            Args:
                cls: The writer class.

            Kwargs:
                force: Replace format/key if exists, default False.
                key: An alternate key to store, default is the writer's format.
            
            Returns:
                The writer class.
            """
        @overload
        def register(self, /, *, key: str = ..., force: bool = ...) -> Callable[[type[_TWT]], type[_TWT]]:
            """Decorator factory for registering with options.

            Kwargs:
                force: Replace format/key if exists.
                key: An alternate key to store, default is the writer's format.
            
            Returns:
                Class decorator factory.
            """

registry = Registry()
"The default tableau writer class registry."

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
        import jinja2
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

class DocBuilder:

    from ..tools.doc import nodez
    from docutils import nodes
    struct_flag_classnames = (
        'has_open',
        'has_closed',
        'leaf',
        'open',
        'closed',
        'is_only_branch')
    struct_data_classnames = (
        'depth',
        'width',
        'left',
        'right',
        'step')

    def __init__(self, tab: Tableau, /):
        self.tab = tab
        self.doc = self.nodes.document(None, None)

    def build(self):
        self.doc += self.build_struct_node(self.tab.tree)

    def build_struct_node(self, s: TreeStruct, /):
        is_child = not s.root
        attrs = dict(
            id=f'structure_{s.id}',
            classes=qset(self.get_struct_classes(s)))
        attrs.update(
            (f'data-{a}', s[a])
            for a in self.struct_data_classnames)
        if s.closed:
            attrs['data-closed-step'] = s.closed_step
        if s.branch_id:
            attrs['data-branch-id'] = s.branch_id
        if s.model_id:
            attrs['data-model-id'] = s.model_id
        node = self.nodez.block(**attrs)
        node += self.build_node_segment(s)
        if s.children:
            node += self.nodez.block(**dict(
                {'data-step': s.branch_step},
                classes=['vertical-line']))
            width = 100 * s.balanced_line_width
            margin = 100 * s.balanced_line_margin
            node += self.nodez.block(**dict(
                {'data-step': s.branch_step},
                classes=['horizontal-line'],
                style=f'width: {width}%; margin-left: {margin}%;'))
            for child in s.children:
                node += self.build_struct_child(s, child)
        if not is_child:
            node += self.nodez.block(classes=['clear'])
        return node

    def build_struct_child(self, s: TreeStruct, child: TreeStruct, /):
        width = (100 / s.width) * child.width
        node = self.nodez.block(**dict({
            'data-step': child.step,
            'data-current-width-pct': f'{width}%'},
            classes=['child-wrapper'],
            style=f'width: {width}%;'))
        node += self.build_struct_node(child)
        return node

    def build_node_segment(self, s: TreeStruct,/):
        is_child = not s.root
        node = self.nodez.block(classes=['node-segment'])
        if is_child:
            attrs = dict({'data-step': s.step}, classes=['vertical-line'])
            node += self.nodez.block(**attrs)
        for n, step in zip(s.nodes, s.ticksteps):
            node += self.build_node_node(n, step)
        return node

    def build_node_node(self, n: Node, tickstep: int, /):
        is_ticked = getattr(n, 'ticked', False)
        classes = qset({'node'})
        if is_ticked:
            classes.add('ticked')
        attrs = dict(id=f'node_{n.id}', classes=classes)
        attrs.update({'data-node-id': n.id, 'data-step': n.step})
        if is_ticked:
            attrs['data-ticked-step'] = tickstep
        node = self.nodez.block(**attrs)
        ...
        return node

    def build_props_node(self, n: Node, tickstep: int, /):
        is_ticked = getattr(n, 'ticked', False)
        classes = qset(('node-props'))
        if is_ticked:
            classes.add('ticked')
        node = self.nodes.inline(
            classes=classes)
        if n.has('sentence'):
            ...
            if n.has('world'):
                ...
        if n.has('designated'):
            classes = qset(('designated'))
            if n['designated']:
                classes.add('designated')
            else:
                classes.add('undesignated')
            node == self.nodes.inline(classes=classes)
        if n.is_access:
            ...
        if n.has('ellipsis'):
            node += self.nodes.inline(classes=['ellipsis'])
        if n.has('is_flag'):
            node += self.nodes.inline(
                classes=['flag', n['flag']],
                title=n['info'])
        return node

    def get_struct_classes(self, s: TreeStruct, /):
        yield 'structure'
        if s.root:
            yield 'root'
        yield from (c for c in self.struct_flag_classnames if s.get(c))
