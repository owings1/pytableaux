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

from docutils.parsers.rst.roles import _roles
from docutils.parsers.rst.roles import set_classes
import enum
import os
import re
import sphinx.directives
from sphinx.util import docstrings, logging
from sphinx.util.docutils import SphinxRole
from sphinx.util.typing import RoleFunction
from typing import Any, Generic, NamedTuple, overload, TYPE_CHECKING
if TYPE_CHECKING:
    from sphinx.application import Sphinx

import lexicals
from lexicals import (
    LexWriter,
    Notation,
    Parser,
    Predicates,
    RenderSet,
)
from tools import abstract, closure
from tools.typing import T

_helpers  = {}
def gethelper(app: Sphinx) -> Helper:
    return _helpers[app]

class SphinxEvent(str, enum.Enum):
    IncludeRead = 'include-read'

class BaseRole(SphinxRole):
    @property
    def helper(self):
        return gethelper(self.env.app)

class BaseDirective(sphinx.directives.SphinxDirective):
    @property
    def helper(self):
        return gethelper(self.env.app)
    arguments: list[str]
    options: dict[str, Any]

    def set_classes(self):
        set_classes(self.options)
        return self.options.get('classes', [])

class Processor:

    app: Sphinx

    @property
    def helper(self) -> Helper:
        return gethelper(self.app)

    @abstract
    def run(self):
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
    return role_entry(roleish).inst

def role_name(roleish: type|RoleFunction) -> str|None:
    return role_entry(roleish).name

class __RoleItem(NamedTuple):
    name: str
    inst: Any

class _RoleItem(__RoleItem, Generic[T]):
    name: str
    inst: T


logger = logging.getLogger(__name__)

class Helper:

    _defaults = dict(
        template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../doc/templates')
        ),
        truth_table_tmpl = 'truth_table.jinja2',
        truth_tables_rev = True,
        wnotn = 'standard',
        pnotn = 'standard',
        preds = lexicals.Predicates(lexicals.Predicate.gen(3))
    )

    def __init__(self, **opts):
        self.reconfigure(opts)

    def reconfigure(self, opts: dict):

        from proof.writers import TabWriter
        import jinja2

        self.opts = opts = dict(self._defaults) | opts

        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(opts['template_dir']),
            trim_blocks = True,
            lstrip_blocks = True,
        )

        opts['preds'] = Predicates(opts['preds'])
        self.parser = Parser(opts['pnotn'], opts['preds'])

        wnotn = Notation(opts['wnotn'])
        self.lwhtml = LexWriter(wnotn, 'html')

        self.pwhtml = TabWriter('html',
            lw = self.lwhtml,
            # classes = ('example', 'rule'),
        )

        # Make a RenderSet that renders subscript 2 as n.
        rskey = 'docutil.trunk'
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

        self.pwtrunk = TabWriter('html',
            lw = LexWriter(wnotn, renderset = rstrunk),
            classes = ('example', 'build-trunk'),
        )
        self._simple_replace = None
        self._line_replace   = None

    def render(self, template: str, *args, **kw) -> str:
        return self.jenv.get_template(template).render(*args, **kw)

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    def sphinx_simple_replace_source(self, app: Sphinx, docname: str, lines: list[str]):
        'Regex replace in a docstring using ``re.sub()``.'
        self._simple_replace_common(lines, mode = 'source')

    def sphinx_simple_replace_include(self, app: Sphinx, lines: list[str]):
        'Regex replace for custom include-read event.'
        self._simple_replace_common(lines, mode = 'include')

    def sphinx_simple_replace_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        'Regex replace for autodoc event.'
        self._simple_replace_common(lines)

    @closure
    def _simple_replace_common():

        def getdefns(self: Helper):
            defns = self._simple_replace
            if defns is not None:
                return defns

            from tools.doc import roles, role_name
            rolewrap = {
                roles.metadress: ['prefixed'],
                roles.refplus  : ['logicref'],
            }
            defns = []
            for rolecls, patnames in rolewrap.items():
                name = role_name(rolecls)
                if name is not None:
                    rep = f':{name}:'r'`\1`'
                    for patname in patnames:
                        pat = rolecls.patterns[patname]
                        pat = re.compile(r'(?<!`)' + rolecls.patterns[patname])
                        defns.append((pat, rep))

            self._simple_replace = defns
            return defns

        def common(self: Helper, lines: list[str], mode: str = None):
            defns = getdefns(self)
            text = '\n'.join(lines)
            count = 0
            for pat, rep in defns:
                text, num = pat.subn(rep, text)
                count += num
            if count:
                if mode == 'source':
                    lines[0]= text
                else:
                    lines.clear()
                    lines.extend(text.split('\n'))

        return common