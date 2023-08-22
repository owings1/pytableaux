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

# del(_package_info)


from . import errors as errors
from . import tools as tools



from . import examples as examples
from . import lang as lang
from . import logics as logics
from . import models as models
from . import proof as proof



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


