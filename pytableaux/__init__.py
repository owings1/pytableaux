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
pytableaux
----------

"""
from __future__ import annotations

# ----- package info

from pytableaux._package_info import package

__docformat__ = package.docformat

_package_info = None
del(_package_info)

# ----- errors, tools

from pytableaux import errors, tools

import pytableaux.tools.abcs
import pytableaux.tools.hooks

# @tools.closure
# def _():

#     # Back patch abcs.hookutil
#     from pytableaux.tools import abcs, hooks
#     abcs.hookutil = hooks.hookutil

    # Rebase errors.Emsg

    # errors.Emsg = abcs.Emsg = abcs._em_rebase(errors.Emsg, errors.EmsgBase, abcs.Ebc)

    # errors.EmsgBase = None
    # del(errors.EmsgBase)

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
        DOC_MODE = tools.sbool(env.get('DOC_MODE', '')),
    )

del(dataclasses,_Settings)

# ---- tools

# import pytableaux.tools.decorators
import pytableaux.tools.sets
from pytableaux.tools.sets import EMPTY_SET

import pytableaux.tools.timing
import pytableaux.tools.mappings
import pytableaux.tools.sequences
import pytableaux.tools.hybrids
import pytableaux.tools.linked

# ------ lang

import pytableaux.lang.collect
import pytableaux.lang.writing
import pytableaux.lang.parsing

@tools.closure
def _():
    from pytableaux.lang import RenderSet, Notation, _symdata
    from pytableaux.lang.parsing import ParseTable

    RenderSet._initcache(Notation, _symdata.rendersets())
    ParseTable._initcache(Notation, _symdata.parsetables())

import pytableaux.lang._repr

@tools.closure
def _():

    from pytableaux.lang import lex
    from pytableaux.lang import LangCommonEnum
    from pytableaux.lang.collect import Argument, Predicates
    from pytableaux.lang.lex import Lexical, LexicalAbc
    for c in (
        LangCommonEnum,
        LexicalAbc,
        Predicates,
        Argument,
        Lexical,
    ):
        c._readonly = True

    lex.nosetattr.enabled = True
    lex.nosetattr.cache.clear()

    del(lex.nosetattr,)

# ----- logics, examples, models
import pytableaux.logics

import pytableaux.proof
import pytableaux.proof.common
import pytableaux.proof.tableaux
import pytableaux.proof.rules
import pytableaux.proof.helpers
import pytableaux.proof.filters
import pytableaux.proof.writers

# ----- proof
import pytableaux.models
import pytableaux.examples


# pytableaux.proof.Rule = pytableaux.proof.tableaux.Rule


__all__ = (
    'errors',
    'examples',
    'logics',
    'models',
    'package',
    'proof',
    'tools',
    'EMPTY_SET',
)


del(
    _,
    pytableaux,
)
