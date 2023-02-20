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

# _package_info = None
del(_package_info)

# ----- errors, tools

from . import errors as errors
from . import tools as tools

# import pytableaux.tools.abcs
# import pytableaux.tools.hooks

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

# ---- tools

from .tools import EMPTY_SET

# import pytableaux.tools.timing
# import pytableaux.tools.hybrids
# import pytableaux.tools.linked

# ------ lang
# import pytableaux.lang
# import pytableaux.lang.collect
# import pytableaux.lang.writing
# import pytableaux.lang.parsing

@tools.closure
def _():
    from .lang import RenderSet, Notation, _symdata
    from .lang.parsing import ParseTable

    RenderSet._initcache(Notation, _symdata.rendersets())
    ParseTable._initcache(Notation, _symdata.parsetables())

    from .lang import _repr as _repr

# import pytableaux.lang._repr

@tools.closure
def _():

    from .errors import Emsg
    from .lang import lex
    from .lang import LangCommonEnum, LangCommonEnumMeta
    from .lang.collect import Argument, Predicates
    from .lang.lex import Lexical, LexicalAbc
    LangCommonEnumMeta.__delattr__ = Emsg.ReadOnly.razr
    LangCommonEnum.__delattr__ = Emsg.ReadOnly.razr
    for c in (
        LangCommonEnum,
        LexicalAbc,
        Predicates,
        Argument,
        Lexical,
    ):
        pass
        c._readonly = True

    lex.nosetattr.enabled = True
    lex.nosetattr.cache.clear()

    del(lex.nosetattr,)

# import pytableaux.logics

# import pytableaux.proof
# import pytableaux.proof.common
# import pytableaux.proof.tableaux
# import pytableaux.proof.rules
# import pytableaux.proof.helpers
# import pytableaux.proof.filters
# import pytableaux.proof.writers

# import pytableaux.models
# import pytableaux.examples

from . import errors as errors
from . import examples as examples
from . import logics as logics
from . import models as models
from . import proof as proof

# pytableaux.proof.Rule = pytableaux.proof.tableaux.Rule


__all__ = (
    'errors',
    'examples',
    'logics',
    'models',
    'package',
    'proof',
    'tools',
    # 'EMPTY_SET',
)


del(
    _,
    # pytableaux,
    )
