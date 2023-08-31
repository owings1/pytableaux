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
#
# Python domain:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html?#the-python-domain
#
# Autodoc directives:
#    https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directives
#
# Built-in roles:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html
#
# Sphinx events:
#    https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
#
# Docutils doctree:
#    https://docutils.sourceforge.io/docs/ref/doctree.html
#
# Font (GPL):
#    http://www.gust.org.pl/projects/e-foundry/tg-math/download/index_html#Bonum_Math
#
# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html
"""
pytabdoc package (pytableaux doc tools)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from __future__ import annotations

import os
import sys

_dir = os.path.abspath(f'{os.path.dirname(__file__)}/../..')
if _dir not in sys.path:
    sys.path.append(_dir)
del(_dir)

from pytableaux.logics import *
import warnings
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from types import MappingProxyType as MapProxy
from typing import Any, NamedTuple, TypeVar

import jinja2
import sphinx.directives
import sphinx.directives.code
from docutils.parsers.rst.roles import _roles
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.environment import BuildEnvironment
from sphinx.ext import viewcode
from sphinx.util import logging
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.docutils import SphinxRole




from pytableaux import errors, logics
from pytableaux.lang import Parser, Predicates
from pytableaux.tools import EMPTY_MAP, EMPTY_SET, abcs, dictns, qset

__all__ = (
    'AutodocProcessor',
    'BaseDirective',
    'BaseRole',
    'ConfKey',
    'DirectiveHelper',
    'Processor',
    'ReplaceProcessor',
    'role_entry',
    'role_instance',
    'role_name',
    'RoleItem',
    'SphinxEvent',
    'Tabler')

_T = TypeVar('_T')

NOARG = object()

logger = logging.getLogger(__name__)

# ------------------------------------------------

class SphinxEvent(str, Enum):
    'Custom Sphinx event names.'

    IncludeRead = 'include-read'

class ConfKey(str, Enum):
    'Custom config keys.'

    copy_file_tree = 'copy_file_tree'
    "The config key for file tree copy actions."

    delete_file_tree = 'delete_file_tree'
    "The config key for file tree delete actions."

    auto_skip_enum_value = 'autodoc_skip_enum_value'

    wnotn   = 'write_notation'
    wfmt =  'write_format'
    strings =  'strings_table'
    pnotn = 'parse_notation'
    preds = 'parse_predicates'

    truth_table_template = 'truth_table_template'
    truth_table_reverse = 'truth_table_reverse'

    templates_path = 'templates_path'

# ------------------------------------------------

APPSTATE: dict[Sphinx, dict] = {}
"Storage for stateful info for Sphinx app. Removed on build-finished."

def setup(app: Sphinx):

    from . import directives, nodez, processors, roles, tables

    APPSTATE[app] = {}
    app.connect('config-inited', init_app)
    app.connect('build-finished', lambda *_: APPSTATE.pop(app))
    # app.connect('viewcode-find-source', test_handler)

    nodez.setup(app)
    directives.setup(app)
    tables.setup(app)
    processors.setup(app)
    roles.setup(app)

def init_app(app: Sphinx, config: Config):
    paths = [
        os.path.join(app.srcdir, tp) for tp in
        config[ConfKey.templates_path]]
    APPSTATE[app][jinja2.Environment]  = jinja2.Environment(
        loader = jinja2.FileSystemLoader(paths),
        trim_blocks = True,
        lstrip_blocks = True)
    if not sys.warnoptions:
        warnings.simplefilter('ignore', category=errors.RepeatValueWarning)

def test_handler(app, modname):
    print('\n' * 3, app, modname, '\n' * 3)
# ------------------------------------------------

def viewcode_target(obj):
    if isinstance(obj, str):
        modname = obj
    else:
        modname = obj.__module__
    return f"{viewcode.OUTPUT_DIRNAME}/{modname.replace('.', '/')}"

class AppEnvMixin(abcs.Abc):

    app: Sphinx
    env: BuildEnvironment
    config: Config

    @property
    def appstate(self) -> dict:
        return APPSTATE[self.app]

    @property
    def jenv(self) -> jinja2.Environment:
        "jinja2 Environment"
        return self.appstate[jinja2.Environment]

    @property
    def current_module(self):
        return import_module(self.env.ref_context['py:module'])

    @property
    def current_class(self):
        return getattr(self.current_module, self.env.ref_context['py:class'])

    @property
    def current_logic(self):
        return logics.registry(self.current_module)

    def viewcode_target(self, obj = None):
        if obj is None:
            obj = self.current_module
        return viewcode_target(obj)

class RenderMixin(AppEnvMixin):

    def render(self, template, *args, **kw):
        return self.jenv.get_template(template).render(*args, **kw)

# ------------------------------------------------

class RoleDirectiveMixin(AppEnvMixin):

    option_spec = EMPTY_MAP

    options: dict

    def set_classes(self, opts = NOARG, /) -> qset[str]:
        if opts is NOARG:
            opts = self.options
        return qset(set_classes(opts).get('classes', EMPTY_SET))

    def parse_opts(self, rawopts):
        optspec = self.option_spec
        todo = dict(rawopts)
        builder = {}
        if optspec.get('classes') is optspecs.classes:
            if 'classes' in set_classes(todo):
                builder['classes'] = todo.pop('classes')
        builder.update({
            key: optspec[key](value)
            for key, value in todo.items()})
        return builder

    @abstractmethod
    def run(self): ...

class LogicOptionMixin(RoleDirectiveMixin):

    @property
    def logic(self) -> logics.LogicType:
        try:
            return self.options['logic']
        except KeyError:
            return self.current_logic

    @logic.setter
    def logic(self, value):
        self.options['logic'] = logics.registry(value)

class ParserOptionMixin(RoleDirectiveMixin):

    def parser_option(self) -> Parser:
        opts, conf = self.options, self.config
        return Parser(opts.get(ConfKey.pnotn, opts.get('pnotn', conf[ConfKey.pnotn])),
            Predicates(opts.get(ConfKey.preds, opts.get('preds', conf[ConfKey.preds]))))

# ------------------------------------------------

class BaseDirective(sphinx.directives.SphinxDirective, RoleDirectiveMixin):

    arguments: list[str]

    @property
    def app(self) -> Sphinx:
        self.error
        return self.env.app

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
    def app(self):
        return self.inst.app

    @property
    def config(self):
        return self.inst.config

    @property
    def options(self):
        return self.inst.options

# ------------------------------------------------

class BaseRole(SphinxRole, RoleDirectiveMixin):

    patterns = {}

    @property
    def app(self) -> Sphinx:
        return self.env.app

    def __init__(self):
        self.options = {'class': None}

    def wrapped(self, name, newopts, newcontent: list = [], /):
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

class Processor(AppEnvMixin):

    __slots__ = EMPTY_SET

    @property
    def env(self) -> BuildEnvironment:
        return self.app.env

    @property
    def config(self) -> Config:
        return self.app.config

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

# ------------------------------------------------

class AutodocProcessor(Processor):

    @dataclass
    class Record(dictns):
        what: str
        name: str
        obj: Any
        options: dict
        lines: list[str]

    app: Sphinx
    lines: list[str]
    record: AutodocProcessor.Record

    def hastext(self, txt:str):
        return txt in '\n'.join(self.lines)

    def applies(self):
        return True

    def __call__(self, app:Sphinx, *args):
        self.app = app
        self.record = self.Record(*args)
        self.lines = self.record.lines
        if self.applies():
            self.run()

    def __iadd__(self, other: str|list[str]):
        self.lines.extend(self.prepstr(other))
        return self

    def prepstr(self, s: str|list[str], **kw) -> list[str]:
        if not isinstance(s, str):
            s = '\n'.join(s)
        return prepare_docstring(s, **kw)

# ------------------------------------------------

class ReplaceProcessor(Processor):

    event: str
    mode: str
    lines: list[str]
    args: tuple[Any, ...]

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

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

class Tabler(list, abcs.Abc):

    header: list[str]
    body: list
    meta: dict

    def __init__(self, body, header, /, **meta):
        self.header = header
        self.body = body
        self.meta = meta
        self.append(header)
        self.extend(body)

    def apply_repr(self, reprfunc, /) -> Tabler:
        for row in self:
            for i, v in enumerate(row):
                if not isinstance(v, str):
                    row[i] = reprfunc(v)
        return self

    def tb(self, tablefmt = None, *, rp = None, **kw):
        from tabulate import tabulate as tb
        if rp:
            self.apply_repr(rp)
        return tb(self.body, self.header, tablefmt, **kw)


# ------------------------------------------------




# ------------------------------------------------


def set_classes(opts:dict):
    if 'class' in opts:
        if opts['class'] is None:
            del(opts['class'])
        else:
            if 'classes' in opts:
                raise TypeError(f"both 'class' and 'classes' in options: {opts}")
            opts['classes'] = opts.pop('class')
    return opts

# ------------------------------------------------

class RoleItem(NamedTuple):
    name: str
    inst: object

def role_entry(roleish):
    'Get loaded role name and instance, by name, instance or type.'
    idx = _roles
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

def role_instance(roleish: type[_T]|str) -> _T|BaseRole:
    'Get loaded role instance, by name, instance or type.'
    return role_entry(roleish).inst

def role_name(roleish):
    'Get loaded role name, by name, instance or type.'
    return role_entry(roleish).name

from . import optspecs
