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
# pytableaux.logics.s5 tests
from __future__ import annotations

from ..utils import BaseCase
from .test_cpl import TestTables as BaseTables


class Base(BaseCase):
    logic = 'S4'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_valid_s4_complex_possibility_with_max_steps(self):
        self.valid_tab('MNb:LCaMMMNb:Ma', max_steps = 200)

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx:LMSxFx', build_timeout = 1000)

    def test_invalid_problematic_1_with_timeout(self):
        self.invalid_tab('b:LMa', build_timeout = 2000)

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc:LCaMNb:Ma')
        # model.add_access(0, 1)
        # model.add_access(1, 2)
        # model.finish()
        # assert 2 in model.visibles(0)

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):

        # Rule ordering benchmark result:
        
        #           [# non-branching rules]
        #                 [S4:Transitive]
        #           [Necessity, Possibility]
        #                 [T:Reflexive]
        #           [# branching rules]
        #         - [Existential, Universal]
        #                 [S5:Symmetric]
        #             [D:Serial],
        #       S5: 8 branches, 142 steps
        #       S4: 8 branches, 132 steps
        #        T: 8 branches, 91 steps
        #        D: 8 branches, 57 steps

        # 200 might be agressive
        self.invalid_tab('b:LVxSyUFxLMGy', max_steps = 200)

class TestTables(Base, BaseTables): pass

class TestModels(Base):

    def test_model_finish_transitity_visibles(self):
        with self.m() as m:
            m.R.add((0,1))
            m.R.add((1,2))
        self.assertIn(2, m.R[0])