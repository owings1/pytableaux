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

import itertools
import os.path
import re
import shutil
import traceback
from dataclasses import dataclass
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Generic, Mapping,
                    Optional)

import jinja2
import sphinx.directives
from docutils import nodes
from docutils.parsers.rst.directives import class_option
from docutils.parsers.rst.roles import _roles
from pytableaux.errors import check
from pytableaux.lang import Notation
from pytableaux.lang.collect import Predicates
from pytableaux.lang.lex import Operator
from pytableaux.lang.writing import LexWriter, RenderSet
from pytableaux.proof import writers
from pytableaux.tools import (EMPTY_MAP, MapProxy, NameTuple, abcs, abstract,
                              closure)
from pytableaux.tools.hybrids import qset
from pytableaux.tools.mappings import dmapns
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.typing import T
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
)


logger = logging.getLogger(__name__)

_helpers: Mapping[Sphinx, Helper] = None
"The Shinx application ``Helper`` instances."

def spaceargs(arg: str, /) -> list[str]:
    return arg.strip().split(' ')

@closure
def app_setup():

    global _helpers

    helpers: dict[Sphinx, Helper]  = {}
    _helpers = MapProxy(helpers)

    def setup(app: Sphinx):
        'Setup the Sphinx application.'

        app.add_config_value(ConfKey.options, {}, 'env', [dict])
        app.add_config_value(ConfKey.htmlcopy, [], 'env', [list[HtmlCopyEntry]])

        from pytableaux.tools.doc import (directives, docparts, processors,
                                          roles)
        directives.setup(app)
        docparts.setup(app)
        processors.setup(app)
        roles.setup(app)

        app.connect('config-inited', init)
        app.connect('build-finished', finish)

    def init(app: Sphinx, config: sphinx.config.Config):

        if app in helpers:
            raise ValueError(f"app already initialized.")

        for entry in config[ConfKey.htmlcopy]:
            validate_copy_entry(entry)

        opts = dict(config[ConfKey.options])

        # Add app templates_path to search path.
        opts['templates_path'] = [
            os.path.join(app.srcdir, tp)
            for tp in itertools.chain(
                opts.get('templates_path', ()),
                config['templates_path'],
            )
        ]

        helpers[app] = Helper(**opts)

    def finish(app: Sphinx, exception: Exception|None):

        if app.builder.format == 'html':
            for entry in app.config[ConfKey.htmlcopy]:
                do_copy_entry(app, entry)

        del helpers[app]

    return setup

def validate_copy_entry(entry: HtmlCopyEntry):
    check.inst(entry, (list, tuple))
    src, dest = entry[0:2]
    eopts = entry[2] if len(entry) > 2 else {}
    check.inst(src, str)
    check.inst(dest, str)
    check.inst(eopts, dict)

def do_copy_entry(app: Sphinx, entry: HtmlCopyEntry):
    src = os.path.join(app.srcdir, entry[0])
    dest = os.path.join(app.outdir, entry[1])
    eopts = dict(entry[2]) if len(entry) > 2 else {}
    eopts.setdefault('dirs_exist_ok', True)
    ignore = eopts.get('ignore')
    if ignore is not None:
        if not callable(ignore):
            if isinstance(ignore, str):
                ignore = ignore,
            eopts['ignore'] = shutil.ignore_patterns(*ignore)
    shutil.copytree(src, dest, **eopts)

def app_helper(app: Sphinx) -> Helper:
    'Get the helper instance from the Sphinx app instance'
    return _helpers[app]

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

class Helper(abcs.Abc):

    __slots__ = (
        'jenv',
        'opts',
        'pwtrunk',
    )

    defaults = dict(
        wnotn = 'standard',
        pnotn = 'standard',
        preds = ((0,0,1), (1,0,1), (2,0,1)),
        truth_table_template = 'truth_table.jinja2',
        truth_table_reverse = True,
        templates_path = (),
    )

    def __init__(self, **opts):
        self.reconfigure(opts)

    def reconfigure(self, opts: dict):

        self.opts = opts = dict(self.defaults) | opts

        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(opts['templates_path']),
            trim_blocks = True,
            lstrip_blocks = True,
        )

        opts['preds'] = Predicates(opts['preds'])

        wnotn = Notation(opts['wnotn'])

        # Make a RenderSet that renders subscript 2 as 'n'.
        rskey = f'{type(self).__qualname__}.trunk'
        try:
            rstrunk = RenderSet.fetch(wnotn, rskey)
        except KeyError:
            rshtml = RenderSet.fetch(wnotn, 'html')
            rstrunk = RenderSet.load(wnotn, rskey, dict(rshtml.data,
                name = f'{wnotn.name}.{rskey}',
                renders = dict(rshtml.renders,
                    subscript = lambda sub: (
                        '<sub>%s</sub>' % ('n' if sub == 2 else sub)
                    )
                )
            ))

        self.pwtrunk = writers.TabWriter('html',
            lw = LexWriter(wnotn, renderset = rstrunk),
            classes = ('example', 'build-trunk'),
        )

    def render(self, template: str, *args, **kw) -> str:
        "Render a jinja2 template from the template path."
        return self.jenv.get_template(template).render(*args, **kw)

class SphinxEvent(str, abcs.Ebc):
    'Custom Sphinx event names.'

    IncludeRead = 'include-read'

class ConfKey(str, abcs.Ebc):
    'Custom config keys.'

    options = 'pt_options'
    "The config key for helper options."

    htmlcopy = 'pt_htmlcopy'
    "The config key for html copy actions."

def set_classes(opts: dict) -> dict:
    if 'class' in opts:
        if opts['class'] is None:
            del(opts['class'])
        else:
            if 'classes' in opts:
                raise TypeError(f"both 'class' and 'classes' in options: {opts}")
            opts['classes'] = opts.pop('class')
    return opts

NOARG = object()

class RoleDirectiveMixin(abcs.Abc):

    env: BuildEnvironment
    option_spec: ClassVar[Mapping[str, Callable]] = EMPTY_MAP

    options: dict[str, Any]

    @property
    def helper(self):
        return app_helper(self.env.app)

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
        try:
            builder.update({
                key: optspec[key](value)
                for key, value in todo.items()
            })
        except KeyError:
            raise
        return builder

class BaseDirective(sphinx.directives.SphinxDirective, RoleDirectiveMixin):

    arguments: list[str]

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

class DirectiveHelper:

    arg_parser = staticmethod(spaceargs)

    required_arguments = 0
    optional_arguments = 0

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

    @abstract
    def run(self): ...

class Processor(abcs.Abc):

    __slots__ = EMPTY_SET

    app: Sphinx

    @property
    def helper(self) -> Helper:
        return app_helper(self.app)

    @abstract
    def run(self) -> None:
        raise NotImplementedError

class AutodocProcessor(Processor):

    @dataclass
    class Record(dmapns):
        what: str
        name: str
        obj: Any
        options: dict
        lines: list[str]

    __slots__ = 'app', 'lines', 'record'

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

class RoleItem(NameTuple, Generic[T]):
    name: str
    inst: T

HtmlCopyEntry = tuple[str, str, Optional[dict]]

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


del(class_option)
