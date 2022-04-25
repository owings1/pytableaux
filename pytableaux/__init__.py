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

@tools.closure
def _():

    # Rebase errors.Emsg

    from pytableaux.tools.abcs import ebcm, Ebc
    errors.Emsg = ebcm.rebase(errors.Emsg, errors.EmsgBase, Ebc)

    errors.EmsgBase = None
    del(errors.EmsgBase)


import pytableaux.tools.typing
import pytableaux.tools.hooks
import pytableaux.tools.decorators
import pytableaux.tools.sets

@tools.closure
def _():
    # Back patch abcm._frozenset

    from pytableaux.tools.abcs import abcm
    abcm._frozenset = pytableaux.tools.sets.setf

import pytableaux.tools.timing
import pytableaux.tools.misc
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
    from pytableaux.lang.lex import Lexical, LexicalItem
    for c in (
        LangCommonEnum,
        LexicalItem,
        Predicates,
        Argument,
        Lexical,
    ):
        c._readonly = True

    lex.nosetattr.enabled = True

    del(lex.nosetattr,)

# ----- logics, examples, models

import pytableaux.logics
import pytableaux.examples
import pytableaux.models

# ----- proof

import pytableaux.proof.types
import pytableaux.proof.common
import pytableaux.proof.filters
import pytableaux.proof.tableaux
import pytableaux.proof.baserules
import pytableaux.proof.helpers
import pytableaux.proof.writers

# from pytableaux import (
#     examples, logics, models, proof, tools
# )

# ---- root aliases

from pytableaux.tools.sets import EMPTY_SET

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


_package_info = None
del(
    _,
    _package_info,
    pytableaux,
)
