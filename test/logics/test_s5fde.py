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
# pytableaux.logics.s5fde tests
from __future__ import annotations

from ..utils import BaseCase
from . import test_fde as FDESuite
from .test_s5 import TestArguments as S5Arguments


class Base(BaseCase):
    logic = 'S5FDE'

class TestRules(Base, autorules=True, bare=True): pass

class TestArguments(Base, autoargs=True):

    test_valid_optimize_nec_rule1 = S5Arguments.test_valid_optimize_nec_rule1

    def test_invalid_intermediate_mix_modal_quantifiers1(self):
        # Countermodels don't work well with quit flags
        self.invalid_tab('MSxGx', ('VxLSyUFxMGy', 'Fm'), max_steps=100, skip_countermodel=True)

class TestTables(Base, FDESuite.TestTables): pass