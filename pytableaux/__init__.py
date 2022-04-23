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
from __future__ import annotations
"""
pytableaux
----------

"""
__docformat__ = 'google'
__all__ = (
    'errors',
    'examples',
    'logics',
    'models',
    'package',
    'proof',
    'tools',
)

from pytableaux import errors

from pytableaux._package_info import package

from pytableaux.tools import abcs

errors.Emsg = abcs.ebcm.rebase(errors.Emsg, errors.EmsgBase, abcs.Ebc)
del(errors.EmsgBase)


import pytableaux.tools.typing
import pytableaux.tools.hooks
# operd, NoSetAttr, lazy, membr, raisr, wraps
import pytableaux.tools.decorators
import pytableaux.tools.sets

# Back patch
abcs.abcm._frozenset = pytableaux.tools.sets.setf

import pytableaux.tools.timing
import pytableaux.tools.misc
import pytableaux.tools.mappings
import pytableaux.tools.sequences
import pytableaux.tools.hybrids
import pytableaux.tools.linked

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

# --------------------------------------------

import pytableaux.logics
import pytableaux.examples
import pytableaux.models

import pytableaux.proof.types
import pytableaux.proof.common
import pytableaux.proof.filters
import pytableaux.proof.tableaux
import pytableaux.proof.baserules
import pytableaux.proof.helpers
import pytableaux.proof.writers

from pytableaux import (
    examples, logics, models, proof, tools
)

from pytableaux.tools.sets import EMPTY_SET


_package_info = None
del(
    _,
    _package_info,
    pytableaux,
)
