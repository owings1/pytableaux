from ..utils import BaseCase
from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

Fa = Predicated.first()

class Base(BaseCase):
    logic = 'CPL'

class TestRules(Base, autorules=True):

    def test_IdentityIndiscernability_not_applies(self):
        tab = self.tab()
        b = tab.branch()
        b += map(self.swnode, ('Fmn', 'Io1o2'))
        rule = tab.rules.get('IdentityIndiscernability')
        self.assertFalse(rule.target(b))

class TestArguments(Base, autoargs=True):

    def test_arguments(self):
        self.invalid_tab('Nb:Bab')
        self.invalid_tab('Nb:NBab')

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FT',
        Negation = 'TF',
        Conjunction = 'FFFT',
        Disjunction = 'FTTT',
        MaterialConditional = 'TTFT',
        MaterialBiconditional = 'TFFT',
        Conditional = 'TTFT',
        Biconditional = 'TFFT',
    )

class TestRuleOptimizations(Base):

    def test_group_score_from_candidate_score(self):
        tab = self.valid_tab('Na:Cab:Nb:Acd')
        self.assertEqual(len(tab), 2)

class TestModels(Base):

    def test_branch_deny_antec(self):
        tab = self.tab('Denying the Antecedent')
        s = Atomic.first()
        m = self.m()
        m.read_branch(tab.open[0])
        self.assertEqual(m.value_of(s), 'F')
        self.assertEqual(m.value_of(~s), 'T')

    def test_branch_extract_disj_2(self):
        tab = self.tab('Extracting a Disjunct 2')
        s = Atomic.first()
        m = self.m()
        m.read_branch(tab.open[0])
        self.assertEqual(m.value_of(s), 'T')
        self.assertEqual(m.value_of(~s), 'F')

    def test_branch_no_proof_predicated(self):
        b = Branch()
        s1 = self.p('Fm')
        b += snode(s1)
        m = self.m()
        m.read_branch(b)
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
        m = self.m()
        m.read_branch(b)
        self.assertEqual(m.value_of(s), 'T')

    def test_opaque_neg_necessity_branch_make_model(self):
        s = self.p('La')
        b = self.tab().branch()
        b += snode(~s)
        with self.m() as m:
            m.read_branch(b)
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
        m = self.m()
        m.finish()
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