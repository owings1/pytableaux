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
# pytableaux - tools.doc package
from __future__ import annotations

__all__ = ()

from docutils.parsers.rst.roles import _roles, set_classes
import enum
import os
import re
import sphinx.directives
from sphinx.util import docstrings, logging
from sphinx.util.docutils import SphinxRole
from typing import (Any, ClassVar, Generic, Mapping, NamedTuple,
                    overload, TYPE_CHECKING)

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    import sphinx.config
    from sphinx.util.typing import RoleFunction

from tools import abstract, closure, MapProxy
from tools.typing import T

logger = logging.getLogger(__name__)

_helpers: Mapping[Sphinx, Helper] = None
"The Shinx application ``Helper`` instances."

PT_CONFKEY = 'pt_options'
"The Sphinx config key for helper options."

@closure
def app_setup():

    global _helpers

    helpers: dict[Sphinx, Helper]  = {}
    _helpers = MapProxy(helpers)

    def setup(app: Sphinx):
        'Setup the Sphinx application.'

        app.add_config_value(PT_CONFKEY, {}, 'env', [dict])

        from tools.doc import directives, processors, roles
        directives.setup(app)
        processors.setup(app)
        roles.setup(app)

        app.connect('config-inited', init)
        app.connect('build-finished', finish)

    def init(app: Sphinx, config: sphinx.config.Config):

        if app in helpers:
            raise ValueError(f"app already initialized.")

        import itertools

        opts = dict(config[PT_CONFKEY])

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
        del helpers[app]

    return setup

def app_helper(app: Sphinx) -> Helper:
    'Get the helper instance from the Sphinx app instance'
    return _helpers[app]

@overload
def role_entry(rolecls: type[T]) -> _RoleItem[T]|None: ...

@overload
def role_entry(rolefn: RoleFunction) -> _RoleItem[RoleFunction]|None: ...

@overload
def role_entry(roleish: str) -> _RoleItem[RoleFunction]|None:...

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
    return _RoleItem(name, inst)

def role_instance(roleish: type[T]) -> T|None:
    'Get loaded role instance, by name, instance or type.'
    return role_entry(roleish).inst

def role_name(roleish: type|RoleFunction) -> str|None:
    'Get loaded role name, by name, instance or type.'
    return role_entry(roleish).name

class Helper:

    defaults = dict(
        templates_path = (),
        wnotn = 'standard',
        pnotn = 'standard',
        preds = ((0,0,1), (1,0,1), (2,0,1)),
        truth_table_template = 'truth_table.jinja2',
        truth_table_reverse = True,
    )

    def __init__(self, **opts):
        self.reconfigure(opts)

    def reconfigure(self, opts: dict):

        import jinja2
        import lexicals
        import proof.writers

        self.opts = opts = dict(self.defaults) | opts

        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(opts['templates_path']),
            trim_blocks = True,
            lstrip_blocks = True,
        )

        opts['preds'] = lexicals.Predicates(opts['preds'])

        wnotn = lexicals.Notation(opts['wnotn'])

        # Make a RenderSet that renders subscript 2 as 'n'.
        rskey = f'{type(self).__qualname__}.trunk'
        try:
            rstrunk = lexicals.RenderSet.fetch(wnotn, rskey)
        except KeyError:
            rshtml = lexicals.RenderSet.fetch(wnotn, 'html')
            rstrunk = lexicals.RenderSet.load(wnotn, rskey, dict(rshtml.data,
                name = f'{wnotn.name}.{rskey}',
                renders = dict(rshtml.renders,
                    subscript = lambda sub: (
                        '<sub>%s</sub>' % ('n' if sub == 2 else sub)
                    )
                )
            ))

        self.pwtrunk = proof.writers.TabWriter('html',
            lw = lexicals.LexWriter(wnotn, renderset = rstrunk),
            classes = ('example', 'build-trunk'),
        )

    def render(self, template: str, *args, **kw) -> str:
        "Render a jinja2 template from the template path."
        return self.jenv.get_template(template).render(*args, **kw)

class SphinxEvent(str, enum.Enum):

    IncludeRead = 'include-read'

class BaseRole(SphinxRole):

    patterns: ClassVar[dict[str, str|re.Pattern]] = {}

    @property
    def helper(self):
        return app_helper(self.env.app)

class BaseDirective(sphinx.directives.SphinxDirective):

    @property
    def helper(self):
        return app_helper(self.env.app)

    arguments: list[str]
    options: dict[str, Any]

    def set_classes(self) -> list[str]:
        set_classes(self.options)
        return self.options.get('classes', [])

class Processor:

    app: Sphinx

    @property
    def helper(self) -> Helper:
        return app_helper(self.app)

    @abstract
    def run(self) -> None:
        raise NotImplementedError

class AutodocProcessor(Processor):

    def applies(self):
        return True

    def __call__(self, app: Sphinx, what: str, name: str, obj: Any, options: dict, lines: list[str]):
        self.app = app
        self.what = what
        self.name = name
        self.obj = obj
        self.options = options
        self.lines = lines
        if self.applies():
            self.run()

    def __iadd__(self, other: str|list[str]):
        if not isinstance(other, str):
            other = '\n'.join(other)
        self.lines.extend(docstrings.prepare_docstring(other))
        return self

class ReplaceProcessor(Processor):

    event: str
    mode: str
    lines: list[str]
    args: tuple[Any, ...]

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

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

class __RoleItem(NamedTuple):
    name: str
    inst: Any

class _RoleItem(__RoleItem, Generic[T]):
    name: str
    inst: T