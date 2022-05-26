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
pytableaux._package_info
^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations
import dataclasses
import os.path
import typing

__docformat__ = 'google'
__all__ = ('package',)

__version__ = 2, 0, 2, 'dev'
'Version tuple (major, minor, patch, release).'

__year__ = 2022
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

def sdata(c: type):
    'Singleton dataclass instance factory.'
    return typing.cast(c, dataclasses.dataclass(init = False)(c)())

@sdata
class package:
    'Package info.'

    name: str = 'pytableaux'

    version: SemVer = SemVer(*__version__)

    author     : object
    license    : object
    repository : object
    issues     : object

    @sdata
    class author:
        name  : str = 'Doug Owings'
        email : str = 'doug@dougowings.net'

    @sdata
    class license:
        id    : str = 'AGPL-3.0-or-later'
        title : str = 'GNU Affero General Public License v3.0 or later'
        url   : str = 'https://www.gnu.org/licenses/agpl-3.0.en.html'

    @sdata
    class repository:
        type : str = 'git'
        url  : str = 'https://github.com/owings1/pytableaux'

    @sdata
    class issues:
        url: str = 'https://github.com/owings1/pytableaux/issues'

    year: int = __year__
    'Last updated year'

    copyright: str = (
        f'2014-{year}, {author.name}. Released under the {license.title}'
    )
    'Project copyright string.'

    root: str = os.path.dirname(os.path.abspath(__file__))
    'Base package directory.'

    docformat: str = __docformat__
    'The doc format.'

    __slots__ = ()
