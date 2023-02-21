from unittest import skip

from pytableaux.errors import *
from pytableaux.proof import *

from .. import BaseCase


class Base(BaseCase):
    logic = 'CFOL'

class TestTabRules(Base):
    def test_rules_not_modal(self):
        for rcls in self.logic.TabRules.all_rules:
            self.assertIs(rcls.modal, False)

class TestArguments(Base):

    def test_valid_syllogism(self):
        self.valid_tab('Syllogism')

    def test_invalid_possibility_addition(self):
        self.invalid_tab('Possibility Addition')

    def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
        self.valid_tab('b', 'VxKFxKaNa')

    def test_invalid_existential_inside_univ_max_steps(self):
        self.invalid_tab('b', 'VxUFxSyFy', max_steps = 100)

class TestModels(Base):

    def test_model_get_data_triv(self):
        m = self.m()
        s1 = self.p('a')
        m.set_literal_value(s1, 'T')
        m.finish()
        self.assertIn('Atomics', m.get_data())

    def test_model_value_of_operated_opaque1(self):
        m = self.m()
        s1 = self.p('La')
        m.set_opaque_value(s1, 'F')
        self.assertEqual(m.value_of_operated(s1.negate()), 'T')

    def test_model_value_of_operated_opaque2(self):
        m = self.m()
        s1 = self.p('La')
        m.set_opaque_value(s1, 'T')
        self.assertEqual(m.value_of_operated(s1), 'T')

    def test_model_read_node_opaque(self):
        m = self.m()
        s1 = self.p('La')
        m._read_node(Node({'sentence': s1}))
        self.assertEqual(m.value_of(s1), 'T')

    def test_model_read_branch_with_negated_opaque_then_faithful(self):
        tab = self.tab('a', ('NLa', 'b'), is_build_models = True)
        m, = tab.models
        s1, s2, s3 = self.pp('a', 'La', 'NLa')
        self.assertEqual(m.value_of(s1), 'F')
        self.assertEqual(m.value_of(s2), 'F')
        self.assertEqual(m.value_of(s3), 'T')
        self.assertTrue(m.is_countermodel_to(tab.argument))

    def test_model_quantified_opaque_is_countermodel(self):
        # For this we needed to add constants that occur within opaque sentences.
        # The use of the existential is important given the way the K model
        # computes quantified values (short-circuit), as opposed to FDE (min/max).
        tab = self.tab('b', 'SxUNFxSyMFy', is_build_models = True)
        arg = tab.argument
        self.assertEqual(len(tab), 2)
        self.assertEqual(len(tab.models), 2)
        m1, m2 = tab.models
        self.assertTrue(m1.is_countermodel_to(arg))
        self.assertTrue(m2.is_countermodel_to(arg))

    def test_model_identity_predication1(self):
        m = self.m()
        s1, s2, s3 = self.pp('Fm', 'Imn', 'Fn')
        for s in (s1, s2):
            m.set_literal_value(s, 'T')
        m.finish()
        self.assertEqual(m.value_of(s3), 'T')

    def test_model_identity_predication2(self):
        m = self.m()
        s1, s2, s3 = self.pp('Fm', 'Imn', 'Fn')
        for s in (s1, s2):
            m.set_literal_value(s, 'T')
        m.finish()
        self.assertEqual(m.value_of(s3), 'T')

    def test_model_self_identity1(self):
        m = self.m()
        s1, s2 = self.pp('Fm', 'Imm')
        # here we make sure the constant m is registered
        m.set_literal_value(s1, 'F')
        m.finish()
        self.assertEqual(m.value_of(s2), 'T')

    def test_model_raises_denotation_error(self):
        m = self.m()
        s1 = self.p('Imm')
        m.finish()
        with self.assertRaises(DenotationError):
            m.value_of(s1)

    def test_model_get_identicals_singleton_two_identical_constants(self):
        m = self.m()
        s1 = self.p('Imn')
        c1, c2 = s1.params
        m.set_literal_value(s1, 'T')
        m.finish()
        identicals = m._get_identicals(c1)
        self.assertEqual(len(identicals), 1)
        self.assertIn(c2, identicals)

    @skip(None)
    def test_model_singleton_domain_two_identical_constants(self):
        m = self.m()
        s1 = self.p('Imn')
        m.set_literal_value(s1, 'T')
        m.finish()
        d = m.frames[0].domain
        self.assertEqual(len(d), 1)

    @skip(None)
    def test_model_same_denotum_two_identical_constants(self):
        m = self.m()
        s1 = self.p('Imn')
        m.set_literal_value(s1, 'T')
        m.finish()
        d1, d2 = (m.get_denotum(c) for c in s1.params)
        self.assertIs(d1, d2)
