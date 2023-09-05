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
pytableaux
----------

"""
from __future__ import annotations

import os.path
import typing
from dataclasses import dataclass

__version__ = 2, 2, 10, 'final'
'Version tuple (major, minor, patch, release).'

__year__ = 2023
'Last updated year, for copyright end date.'

class SemVer(typing.NamedTuple):
    'Version tuple info.'

    major: int
    'Major version number.'

    minor: int
    'Minor version number.'

    patch: int
    'Patch version number.'

    release: str
    'Release tag'

    @property
    def short(self):
        "Short version, e.g. ``'1.2'``"
        return f'{self.major}.{self.minor}'

    @property
    def display(self):
        "Display version, e.g. ``'1.2.3'``"
        return f'{self.short}.{self.patch}'

    @property
    def full(self):
        "Full version, e.g. ``'1.2.3-alpha'``"
        return f'{self.display}-{self.release}'

@dataclass(slots=True)
class Author:
    name: str
    email: str

@dataclass(slots=True)
class License:
    id: str
    title: str
    url: str

@dataclass(slots=True)
class Repository:
    type: str
    url: str

@dataclass(slots=True)
class Issues:
    url: str

@dataclass(slots=True)
class Package:
    'Package info.'
    name: str
    version: SemVer
    author: Author
    license: License
    repository: Repository
    issues: Issues
    root: str
    'Base package directory.'

    @property
    def year(self) -> int:
        'Last updated year'
        return __year__

    @property
    def docformat(self) -> str:
        'The doc format.'
        return __docformat__

    @property
    def copyright(self) -> str:
        'Project copyright string.'
        return (
            f'2014-{self.year}, {self.author.name}. '
            f'Released under the {self.license.title}')

package = Package(
    name = 'pytableaux',
    version = SemVer(*__version__),
    author = Author(
        name = 'Doug Owings',
        email = 'doug@dougowings.net'),
    license = License(
        id = 'AGPL-3.0-or-later',
        title = 'GNU Affero General Public License v3.0 or later',
        url = 'https://www.gnu.org/licenses/agpl-3.0.en.html'),
    repository = Repository(
        type = 'git',
        url = 'https://github.com/owings1/pytableaux'),
    issues = Issues(
        url = 'https://github.com/owings1/pytableaux/issues'),
    root = os.path.dirname(os.path.abspath(__file__)))
'Package info.'


__copyright__ = package.copyright
__license__ = package.license.id
__docformat__ = 'google'

from . import errors as errors
from . import tools as tools

pass

from . import lang as lang
from . import logics as logics
from . import proof as proof
from . import models as models
from . import examples as examples

__all__ = (
    'errors',
    'examples',
    'lang',
    'logics',
    'models',
    'package',
    'proof',
    'tools',
)


