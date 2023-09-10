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
# pytableaux.logics.lp tests
from __future__ import annotations

from pytableaux.lang import Argument

from ..utils import BaseCase


class Base(BaseCase):
    logic = 'LP'

class TestRules(Base, autorules=True): pass
class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FBT',
        Negation = 'TBF',
        Conjunction = 'FFFFBBFBT',
        Disjunction = 'FBTBBTTTT',
        MaterialConditional = 'TTTBBTFBT',
        MaterialBiconditional = 'TBFBBBFBT',
        Conditional = 'TTTBBTFBT',
        Biconditional = 'TBFBBBFBT')

class TestOperatorRules(Base):

    def test_regression_bad_rule_neg_bicond_undes(self):
        tab = self.tab('NBab:NBab', is_build = False)
        rule = tab.rules.get('BiconditionalNegatedUndesignated')
        self.assertTrue(rule.target(tab[0]))
        tab.build()
        self.assertTrue(tab.valid)

class TestModels(Base):

    def test_regression_model_not_a_countermodel(self):
        arg = Argument('NBab:c:BcNUab')
        with self.m() as m:
            for s, v in zip(self.pp(*'abc'), 'FTB'):
                m.set_value(s, v)
        self.assertEqual(m.value_of(arg.premises[1]), 'B')
