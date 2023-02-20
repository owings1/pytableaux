from .. import BaseCase
from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

A = Atomic.first()
Fa = Predicated.first()

class Base(BaseCase):
    logic = 'CPL'

class TestClosureRules(Base):

    def test_ContradictionClosure(self):
        self.rule_eg('ContradictionClosure')

    def test_SelfIdentityClosure(self):
        self.rule_eg('SelfIdentityClosure')

    def test_NonExistenceClosure(self):
        self.rule_eg('NonExistenceClosure')

class TestIdentityRules(Base):

    def test_IdentityIndiscernability(self):
        self.rule_eg('IdentityIndiscernability')

    def test_IdentityIndiscernability_not_applies(self):
        preds = Predicates({(0, 0, 2)})
        s1, s2 = self.pp('Fmn', 'Io1o2', preds)
        tab, b = self.tabb((
            {'sentence': s1, 'world': 0},
            {'sentence': s2, 'world': 0}))
        rule = tab.rules.get('IdentityIndiscernability')
        self.assertFalse(rule.target(b))

class TestArguments(Base):

    def test_arguments(self):
        self.valid_tab('Simplification')
        self.invalid_tab('Syllogism')
        self.invalid_tab('Nb', ('Bab'))
        self.invalid_tab('Nb', ('NBab'))

class TestRuleOptimizations(Base):

    def test_group_score_from_candidate_score(self):
        tab = self.valid_tab('Na', ('Cab', 'Nb', 'Acd'))
        self.assertEqual(len(tab), 2)

class TestModels(Base):

    def test_branch_deny_antec(self):
        tab = self.tab('Denying the Antecedent')
        m = self.m()
        m.read_branch(tab.open[0])
        self.assertEqual(m.value_of(A), 'F')
        self.assertEqual(m.value_of(A.negate()), 'T')

    def test_branch_extract_disj_2(self):
        tab = self.tab('Extracting a Disjunct 2')
        m = self.m()
        m.read_branch(tab.open[0])
        self.assertEqual(m.value_of(A), 'T')
        self.assertEqual(m.value_of(A.negate()), 'F')

    def test_branch_no_proof_predicated(self):
        b = Branch()
        b.add({'sentence': Fa})
        m = self.m()
        m.read_branch(b)
        branch = Branch()
        s1 = self.p('Fm')
        branch.add({'sentence': s1})
        model = self.m()
        model.read_branch(branch)
        self.assertEqual(model.value_of(s1), 'T')

    def test_value_of_operated_opaque(self):
        # coverage
        model = self.m()
        s = self.p('La')
        model.set_opaque_value(s, 'T')
        self.assertEqual(model.value_of_operated(s), 'T')
        
    def test_set_literal_value_predicated1(self):
        model = self.m()
        s = Predicated('Identity', tuple(Constant.gen(2)))
        model.set_literal_value(s, 'T')
        res = model.value_of(s)
        self.assertEqual(res, 'T')

    def test_opaque_necessity_branch_make_model(self):
        s = self.p('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s})
        model = self.m()
        model.read_branch(branch)
        self.assertEqual(model.value_of(s), 'T')

    def test_opaque_neg_necessity_branch_make_model(self):
        s = self.p('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s.negate()})
        model = self.m()
        model.read_branch(branch)
        self.assertEqual(model.value_of(s), 'F')

    def test_get_data_triv(self):
        s = self.p('a')
        model = self.m()
        model.set_literal_value(s, 'T')
        model.finish()
        data = model.get_data()
        self.assertIn('Atomics', data)

    def test_value_of_operated_opaque1(self):
        s1 = self.p('La')
        model = self.m()
        model.set_opaque_value(s1, 'F')
        res = model.value_of_operated(s1.negate())
        self.assertEqual(res, 'T')

    def test_value_of_opaque_unassigned(self):
        s = self.p('La')
        model = self.m()
        res = model.value_of(s)
        self.assertEqual(res, model.unassigned_value)

    def test_set_predicated_false_value_error_on_set_to_true(self):
        s = self.p('Fm')
        model = self.m()
        model.set_literal_value(s, 'F')
        with self.assertRaises(ModelValueError):
            model.set_literal_value(s, 'T')

    def test_get_anti_extension(self):
        # coverage
        s: Predicated = Predicated.first()
        model = self.m()
        anti_extension = model.get_anti_extension(s.predicate)
        self.assertEqual(len(anti_extension), 0)
        model.set_literal_value(s, 'F')
        self.assertIn(s.params, anti_extension)