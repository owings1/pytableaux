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

# ----- package info

from ._package_info import package as package

__docformat__ = package.docformat

del(_package_info)


from . import errors as errors
from . import tools as tools


# ----- env

import dataclasses

@dataclasses.dataclass
class _Settings:
    DEBUG: bool
    ITEM_CACHE_SIZE: int
    DOC_MODE: bool

_ENV: _Settings

@tools.closure
def _():
    from os import environ as env
    global _ENV
    _ENV = _Settings(
        DEBUG = tools.sbool(env.get('DEBUG', '')),
        ITEM_CACHE_SIZE = int(env.get('ITEM_CACHE_SIZE', 1000) or 0),
        DOC_MODE = tools.sbool(env.get('DOC_MODE', '')))

del(dataclasses,_Settings)

from . import examples as examples
from . import logics as logics
from . import models as models
from . import proof as proof



__all__ = (
    'errors',
    'examples',
    'logics',
    'models',
    'package',
    'proof',
    'tools',
)


