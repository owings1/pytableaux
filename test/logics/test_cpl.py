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
# pytableaux.logics.cpl tests
from __future__ import annotations

from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

from ..utils import BaseCase


class Base(BaseCase):
    logic = 'CPL'

class TestRules(Base, autorules=True):

    def test_Disjunction_node(self):
        tab = self.rule_test('DisjunctionNegated').tableau
        s = tab[0][0]['sentence']
        self.assertEqual(s.operator, Operator.Negation)

    def test_IdentityIndiscernability_not_applies(self):
        tab = self.tab()
        b = tab.branch()
        b += map(self.swnode, ('Fmn', 'Io1o2'))
        rule = tab.rules.get('IdentityIndiscernability')
        self.assertFalse(rule.target(b))

    def test_IdentityIndiscernability_not_target_after_apply(self):
        test = self.rule_test('IdentityIndiscernability')
        tab = test.tableau
        b = tab.branch()
        b += map(self.swnode, ['Imn', 'Fs'])
        self.assertFalse(test.rule.target(b))

    def test_IdentityIndiscernability_target_predicate_sentence(self):
        tab = self.tab()
        b = tab.branch()
        rule = tab.rules.get('IdentityIndiscernability')
        b += map(self.swnode, ['Imn', 'Fm'])
        self.assertTrue(rule.target(b))

    def test_IdentityIndiscernability_not_target_self_identity(self):
        tab = self.tab()
        b = tab.branch()
        rule = tab.rules.get('IdentityIndiscernability')
        # need 2 nodes to trigger test, since the rule skips the node if
        # it is the self-same node it is comparing to
        b += map(self.swnode, ['Imn', 'Imn'])
        self.assertFalse(rule.target(b))

    def test_IdentityIndiscernability_skip_self_identity_coverage(self):
        tab = self.tab()
        b = tab.branch()
        rule = tab.rules.get('IdentityIndiscernability')
        b += self.swnode('Imm')
        self.assertFalse(rule.target(b))

    def test_IdentityIndiscernability_not_target_duplicate(self):
        tab = self.tab()
        b = tab.branch()
        rule = tab.rules.get('IdentityIndiscernability')
        b += map(self.swnode, ['Imn', 'Fm', 'Fn'])
        self.assertFalse(rule.target(b))

    def test_optim_group_score_from_candidate_score(self):
        tab = self.valid_tab('Na:Cab:Nb:Acd')
        self.assertEqual(len(tab), 2)

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FT',
        Negation = 'TF',
        Conjunction = 'FFFT',
        Disjunction = 'FTTT',
        MaterialConditional = 'TTFT',
        MaterialBiconditional = 'TFFT',
        Conditional = 'TTFT',
        Biconditional = 'TFFT')

class TestModels(Base):

    def test_branch_deny_antec(self):
        tab = self.tab('Denying the Antecedent')
        m = self.m(tab.open[0])
        s = Atomic.first()
        self.assertEqual(m.value_of(s), 'F')
        self.assertEqual(m.value_of(~s), 'T')

    def test_branch_extract_disj_2(self):
        tab = self.tab('Extracting a Disjunct 2')
        s = Atomic.first()
        m = self.m(tab.open[0])
        self.assertEqual(m.value_of(s), 'T')
        self.assertEqual(m.value_of(~s), 'F')

    def test_branch_no_proof_predicated(self):
        b = Branch()
        s1 = self.p('Fm')
        b += snode(s1)
        m = self.m(b)
        self.assertEqual(m.value_of(s1), 'T')
        
    def test_set_literal_value_predicated1(self):
        s = Predicate.Identity(Constant.gen(2))
        with self.m() as m:
            m.set_literal_value(s, 'T')
        self.assertEqual(m.value_of(s), 'T')

    def test_opaque_necessity_branch_make_model(self):
        s = self.p('La')
        b = self.tab().branch()
        b += snode(s)
        m = self.m(b)
        self.assertEqual(m.value_of(s), 'T')

    def test_opaque_neg_necessity_branch_make_model(self):
        s = self.p('La')
        b = self.tab().branch()
        b += snode(~s)
        m = self.m(b)
        self.assertEqual(m.value_of(s), 'F')

    def test_get_data_triv(self):
        s = self.p('a')
        with self.m() as m:
            m.set_literal_value(s, 'T')
        data = m.get_data()
        self.assertIn('Atomics', data)

    def test_value_of_operated_opaque1(self):
        s1 = self.p('La')
        with self.m() as m:
            m.set_opaque_value(s1, 'F')
        self.assertEqual(m.value_of_operated(~s1), 'T')

    def test_value_of_opaque_unassigned(self):
        s = self.p('La')
        m = self.m().finish()
        self.assertEqual(m.value_of(s), m.Meta.unassigned_value)

    def test_set_predicated_false_value_error_on_set_to_true(self):
        s = self.p('Fm')
        m = self.m()
        m.set_literal_value(s, 'F')
        with self.assertRaises(ModelValueError):
            m.set_literal_value(s, 'T')

    def test_get_anti_extension(self):
        # coverage
        s = Predicated.first()
        m = self.m()
        interp = m.frames[0].predicates[s.predicate]
        self.assertEqual(len(interp.neg), 0)
        m.set_literal_value(s, 'F')
        self.assertIn(s.params, interp.neg)
