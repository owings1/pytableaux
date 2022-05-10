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
"""
pytableaux.tools.doc
^^^^^^^^^^^^^^^^^^^^
"""
from __future__ import annotations

import re
import traceback
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Container, Generic,
                    Mapping)

import sphinx.directives
from docutils import nodes
from docutils.parsers.rst.directives import class_option
from docutils.parsers.rst.roles import _roles
from pytableaux import logics
from pytableaux.lang import Operator, Predicates
from pytableaux.tools import EMPTY_MAP, MapProxy, NameTuple, abcs, abstract
from pytableaux.tools.doc.extension import Helper, helpers
from pytableaux.tools.hybrids import qset
from pytableaux.tools.mappings import dmapns
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.typing import T
from sphinx.ext.autodoc.importer import import_object
from sphinx.util import logging
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.docutils import SphinxRole

if TYPE_CHECKING:
    from typing import overload

    import sphinx.config
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import RoleFunction

__all__ = (
    'app_helper',
    'app_setup',
    'AutodocProcessor',
    'BaseDirective',
    'BaseRole',
    'classopt',
    'cleanws',
    'ConfKey',
    'DirectiveHelper',
    'Helper',
    'nodeopt',
    'opersopt',
    'predsopt',
    'Processor',
    're_comma',
    're_space',
    'ReplaceProcessor',
    'role_entry',
    'role_instance',
    'role_name',
    'RoleItem',
    'SphinxEvent',
    'Tabler',
)

NOARG = object()

logger = logging.getLogger(__name__)

# ------------------------------------------------

class SphinxEvent(str, abcs.Ebc):
    'Custom Sphinx event names.'

    IncludeRead = 'include-read'

# ------------------------------------------------

class ConfKey(str, abcs.Ebc):
    'Custom config keys.'

    options = 'pt_options'
    "The config key for helper options."

    htmlcopy = 'pt_htmlcopy'
    "The config key for html copy actions."

    auto_skip_enum_value = 'autodoc_skip_enum_value'

# ------------------------------------------------

class RoleDirectiveMixin(abcs.Abc):

    env: BuildEnvironment
    option_spec: ClassVar[Mapping[str, Callable]] = EMPTY_MAP

    options: dict[str, Any]

    @abstract
    def run(self): ...

    @property
    def helper(self) -> Helper:
        return helpers[self.env.app]

    def current_module(self):
        return import_module(self.env.ref_context['py:module'])

    def current_class(self):
        return getattr(self.current_module(), self.env.ref_context['py:class'])

    def current_logic(self):
        return logics.registry(self.current_module())

    def set_classes(self, opts = NOARG, /) -> qset[str]:
        if opts is NOARG:
            opts = self.options
        return qset(set_classes(opts).get('classes', EMPTY_SET))

    def parse_opts(self, rawopts: Mapping[str, Any]) -> dict[str, Any]:
        optspec = self.option_spec
        todo = dict(rawopts)
        builder = {}
        if optspec.get('classes', None) is classopt:
            if 'classes' in set_classes(todo):
                builder['classes'] = todo.pop('classes')
        builder.update({
            key: optspec[key](value)
            for key, value in todo.items()
        })
        return builder

# ------------------------------------------------

class BaseDirective(sphinx.directives.SphinxDirective, RoleDirectiveMixin):

    arguments: list[str]

# ------------------------------------------------

class DirectiveHelper(RoleDirectiveMixin):


    required_arguments = 0
    optional_arguments = 0

    @staticmethod
    def arg_parser(arg: str, /) -> list[str]:
        return arg.strip().split(' ')

    inst: BaseDirective
    arguments: list[str]

    def __init__(self, inst: BaseDirective, rawarg: str, /):
        if rawarg is None:
            args = []
        else:
            args = self.arg_parser(rawarg)
        n = len(args)
        if n < self.required_arguments or n > self.optional_arguments:
            raise inst.error('Wrong number of arguments')
        self.arguments = args
        self.inst = inst

    @property
    def env(self):
        return self.inst.env

    @property
    def options(self):
        return self.inst.options

# ------------------------------------------------

class BaseRole(SphinxRole, RoleDirectiveMixin):

    patterns: ClassVar[dict[str, str|re.Pattern]] = {}

    def __init__(self):
        pass
        self.options = {'class': None}

    def wrapped(self, name: str, newopts: Mapping, newcontent: list[str] = [], /):
        "Wrapper for ad-hoc customized roles."
        try:
            buildopts = dict(self.options)
        except AttributeError:
            buildopts = {}
        buildopts.update(self.parse_opts(newopts))
        buildopts = MapProxy(buildopts)

        inst = BaseRole()
        inst.option_spec = MapProxy(dict(self.option_spec))

        def run():

            options = dict(buildopts) | inst.options
            content = newcontent.copy()

            if content and inst.content:
                content += '\n'
            content.extend(inst.content)

            return self(name, inst.rawtext, inst.text, inst.lineno, inst.inliner,
                options, content)

        inst.run = run

        return inst

# ------------------------------------------------

class Processor(abcs.Abc):

    __slots__ = EMPTY_SET

    app: Sphinx

    @property
    def helper(self) -> Helper:
        return helpers[self.app]

    @abstract
    def run(self) -> None:
        raise NotImplementedError

# ------------------------------------------------

class AutodocProcessor(Processor):

    @dataclass
    class Record(dmapns):
        what: str
        name: str
        obj: Any
        options: dict
        lines: list[str]

    __slots__ = 'app', 'lines', 'record'

    def hastext(self, txt:str):
        return txt in '\n'.join(self.lines)

    def applies(self):
        return True

    def __call__(self, app:Sphinx, *args):
        try:
            self.app = app
            self.record = self.Record(*args)
            self.lines = self.record.lines
            if self.applies():
                self.run()
        except Exception as err:
            logger.error(err)
            traceback.print_exc()
            raise

    def __iadd__(self, other: str|list[str]):
        self.lines.extend(self.prepstr(other))
        return self

    def prepstr(self, s: str|list[str], ignore: int = None, tabsize: int = 8) -> list[str]:
        if not isinstance(s, str):
            s = '\n'.join(s)
        return prepare_docstring(s, ignore, tabsize)

# ------------------------------------------------

class ReplaceProcessor(Processor):

    __slots__ = (
        'args',
        'event',
        'lines',
        'mode',
    )

    event: str
    mode: str
    lines: list[str]
    args: tuple[Any, ...]

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    if TYPE_CHECKING:
    
        @overload
        def __call__(self, app: Sphinx, docname: str, lines: list[str]):
            'Regex replace for source-read event.'

        @overload
        def __call__(self, app: Sphinx, lines: list[str]):
            'Regex replace for custom include-read event.'

        @overload
        def __call__(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
            'Regex replace for autodoc event.'

    def __call__(self, *args):
        if len(args) == 2:
            self.event = SphinxEvent.IncludeRead
            self.mode = 'include'
        elif len(args) == 3:
            self.event = 'source-read'
            self.mode = 'source'
        elif len(args) == 6:
            self.event = 'autodoc-process-docstring'
            self.mode = 'autodoc'
        else:
            raise TypeError(f"Unknown event with {len(args)} args")
        self.app = args[0]
        self.lines = args[-1]
        self.args = args
        self.run()

# ------------------------------------------------

class Tabler(list[list[str]]):

    header: list[str]
    body: list[list[str]]
    meta: dict[str, Any]

    __slots__ = 'header', 'body', 'meta'

    def __init__(self, body: list[list[str]], header: list[str]|None, /, **meta):
        self.header = header
        self.body = body
        self.meta = meta
        self.append(header)
        self.extend(body)

    def repr_apply(self, reprfunc: Callable, /) -> Tabler:
        for row in self:
            for i, v in enumerate(row):
                if not isinstance(v, str):
                    row[i] = reprfunc(v)
        return self

    def tb(self, tablefmt = None, *, rp = None, **kw):
        from tabulate import tabulate as tb
        if rp:
            self.repr_apply(rp)
        return tb(self.body, self.header, tablefmt, **kw)

# ------------------------------------------------

if TYPE_CHECKING:

    @overload
    def is_enum_member(modname: str, objpath: list[str]):
        "Prefered method if info is available."

    @overload
    def is_enum_member(fullname: str):
        "Fallback method that tries to guess module path."

def is_enum_member(modname: str, objpath = None):

    if objpath is not None:
        importinfo = import_object(modname, objpath[0:-1])

    else:
        fullpath = modname.split('.')
        if len(fullpath) < 3:
            return False
        objpath = [fullpath[-2], fullpath[-1]]
        modname = '.'.join(fullpath[0:-2])
        while len(modname):
            try:
                importinfo = import_object(modname, objpath[0:-1])
            except ImportError:
                parts = modname.split('.')
                objpath.insert(0, parts.pop())
                modname = '.'.join(parts)
            else:
                break
        else:
            return False

    importobj = importinfo[-1]
    if isinstance(importobj, type) and issubclass(importobj, Enum):
        try:
            _ = importobj(objpath[-1])
        except (ValueError, TypeError) as e:
            logger.debug(e)
            return False
        else:
            return True


# ------------------------------------------------


re_space = re.compile(r'\s')

re_comma = re.compile(r',')

re_nonslug_plus = re.compile(r'[^a-zA-Z0-9_-]+')
"One or more non alpha, num, _ or - chars"

if TYPE_CHECKING:
    @overload
    def classopt(arg: Any) -> list[str]: ...

classopt = class_option

def boolopt(arg: str, /) -> bool:
    if arg:
        arg = arg.strip()
    else:
        arg = 'on'
    arg = arg.lower()
    if arg in ('true', 'yes', 'on'):
        return True
    if arg in ('false', 'no', 'off'):
        return False
    raise ValueError(f"Invalid boolean value: '{arg}'")

def stropt(arg: str, /) -> str:
    if arg is None:
        arg = ''
    return arg

def cleanws(arg: str, /) -> str:
    "Option spec to remove all whitespace."
    return re_space.sub('', arg)

def predsopt(arg: str, /) -> Predicates:
    "Option spec for list of predicate specs."
    return Predicates(
        tuple(map(int, spec.split(':')))
        for spec in re_comma.split(cleanws(arg))
    )

def opersopt(arg: str, /) -> tuple[Operator, ...]:
    return tuple(map(Operator,
        (s.strip() for s in re_comma.split(arg))
    ))

def nodeopt(arg: str, /):
    return getattr(nodes, arg)

def attrsopt(arg: str, /) -> list[str]:
    "list of attr-like names"
    return re_nonslug_plus.sub(' ', arg).split(' ')

def choiceopt(choices: Container, /):
    'Option spec builder for choices.'
    def opt(arg: str, /) -> str:
        if arg not in choices:
            raise ValueError(arg)
        return arg
    return opt

del(class_option)

# ------------------------------------------------


def set_classes(opts: dict) -> dict:
    if 'class' in opts:
        if opts['class'] is None:
            del(opts['class'])
        else:
            if 'classes' in opts:
                raise TypeError(f"both 'class' and 'classes' in options: {opts}")
            opts['classes'] = opts.pop('class')
    return opts

# ------------------------------------------------

class RoleItem(NameTuple, Generic[T]):
    name: str
    inst: T

if TYPE_CHECKING:

    @overload
    def role_entry(rolecls: type[T]) -> RoleItem[T]|None: ...

    @overload
    def role_entry(rolefn: RoleFunction) -> RoleItem[RoleFunction]|None: ...

    @overload
    def role_entry(roleish: str) -> RoleItem[RoleFunction]|None: ...

def role_entry(roleish):
    'Get loaded role name and instance, by name, instance or type.'
    idx: dict = _roles
    if isinstance(roleish, str):
        inst = idx.get(roleish)
        if inst is None:
            return None
        name = roleish
    else:
        checktype = isinstance(roleish, type)
        for name, inst in idx.items():
            if checktype:
                if type(inst) is roleish:
                    break
            elif inst is roleish:
                break
        else:
            return None
    return RoleItem(name, inst)

def role_instance(roleish: type[T]) -> T|None:
    'Get loaded role instance, by name, instance or type.'
    return role_entry(roleish).inst

def role_name(roleish: type|RoleFunction) -> str|None:
    'Get loaded role name, by name, instance or type.'
    return role_entry(roleish).name
