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
import sphinx.directives
from sphinx.util import docstrings
from sphinx.util.docutils import SphinxRole
from sphinx.util.typing import RoleFunction
from typing import Any, Generic, NamedTuple, overload, TYPE_CHECKING
if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from docutil import Helper

from tools import abstract
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
