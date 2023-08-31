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
#
# ------------------
#
# pytableaux.logics.kfde tests
from __future__ import annotations

from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.logics import kfde as KFDE
from pytableaux.proof import *
from pytableaux.proof import rules

from ..utils import BaseCase


class Base(BaseCase):
    logic = KFDE

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNBT',
        Negation = 'TNBF',
        Conjunction = 'FFFFFNNNFNBBFNBT',
        Disjunction = 'FNBTNNBTBBBTTTTT',
        MaterialConditional = 'TTTTNNBTBBBTFNBT',
        MaterialBiconditional = 'TNBFNNBNBBBBFNBT',
        Conditional = 'TTTTNNBTBBBTFNBT',
        Biconditional = 'TNBFNNBNBBBBFNBT')