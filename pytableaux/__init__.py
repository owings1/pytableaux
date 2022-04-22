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
    'lexicals',
    'logics',
    'models',
    'package',
    'parsers',
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
# import pytableaux.tools.callables

import pytableaux.lexicals
import pytableaux.parsers

@tools.closure
def _():
    from pytableaux.lexicals import RenderSet, Notation
    from pytableaux.parsers import ParseTable
    from pytableaux.lang import _symdata

    RenderSet._initcache(Notation, _symdata.rendersets())
    ParseTable._initcache(Notation, _symdata.parsetables())

import pytableaux.lang._repr

@tools.closure
def _():

    from pytableaux import lexicals
    for c in (
        lexicals.LangCommonEnum,
        lexicals.LexicalItem,
        lexicals.Predicates,
        lexicals.Argument,
        lexicals.Lexical,
    ):

        c._readonly = True
    lexicals.nosetattr.enabled = True

    del(lexicals.nosetattr,)

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
    examples, lexicals, logics, models, parsers, proof, tools
)

from pytableaux.tools.sets import EMPTY_SET




