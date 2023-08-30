from __future__ import annotations

from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.logics import k as K
from pytableaux.proof import *
from pytableaux.proof import rules
from pytableaux.proof.tableaux import *

from ..utils import BaseCase


class Base(BaseCase):
    logic = K
    def m(self, *args, **kw) -> K.Model:
        return super().m(*args, **kw)


class TestRules(Base, autorules=True):

    def test_Disjunction_node(self):
        rule, tab = self.rule_eg('DisjunctionNegated', step = False)
        s = tab[0][0]['sentence']
        self.assertEqual(s.operator, Operator.Negation)

    def test_Possibility_node_world_0(self):
        rule, tab = self.rule_eg('Possibility', step = False)
        node = tab[0][0]
        self.assertEqual(node['world'], 0)

    def test_Existential_node_quantifier(self):
        rule, tab = self.rule_eg('Existential', step = False)
        node = tab[0][0]
        self.assertEqual(node['sentence'].quantifier, Quantifier.Existential)

    def test_IdentityIndiscernability_not_target_after_apply(self):
        rule, tab = self.rule_eg('IdentityIndiscernability')
        b = tab.branch()
        b += map(self.swnode, ['Imn', 'Fs'])
        self.assertFalse(rule.target(b))

    def test_IdentityIndiscernability_target_predicate_sentence(self):
        tab, b = self.tabb()
        rule = tab.rules.get(K.Rules.IdentityIndiscernability)
        b += map(self.swnode, ['Imn', 'Fm'])
        self.assertTrue(rule.target(b))

    def test_IdentityIndiscernability_not_target_self_identity(self):
        tab, b = self.tabb()
        rule = tab.rules.get(K.Rules.IdentityIndiscernability)
        # need 2 nodes to trigger test, since the rule skips the node if
        # it is the self-same node it is comparing to
        b += map(self.swnode, ['Imn', 'Imn'])
        self.assertFalse(rule.target(b))

    def test_IdentityIndiscernability_skip_self_identity_coverage(self):
        tab, b = self.tabb()
        rule = tab.rules.get(K.Rules.IdentityIndiscernability)
        b += self.swnode('Imm')
        self.assertFalse(rule.target(b))

    def test_IdentityIndiscernability_not_target_duplicate(self):
        tab, b = self.tabb()
        rule = tab.rules.get(K.Rules.IdentityIndiscernability)
        b += map(self.swnode, ['Imn', 'Fm', 'Fn'])
        self.assertFalse(rule.target(b))

    def test_rules_modal(self):
        for rcls in self.logic.Rules.all():
            self.assertIs(rcls.modal, True)

    def test_Necessity_node_targets(self):
        tab, b = self.tabb()
        b += self.swnode('La', 0), anode(0, 0)
        rule = tab.rules.get(K.Rules.Necessity)
        targets = list(rule._get_node_targets(b[0], b))
        self.assertEqual(len(targets), 1)

    def test_Necessity_node_targets_does_not_duplicate_node(self):
        tab, b = self.tabb()
        b += map(self.swnode, ('a', 'La'))
        b += anode(0, 0)
        rule = tab.rules.get(K.Rules.Necessity)
        targets = list(rule._get_node_targets(b[1], b))
        self.assertEqual(len(targets), 0)


class TestArgument(Base, autoargs=True):

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc', ('LCaMNb', 'Ma'))

    def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
        self.valid_tab('b', 'VxKFxKaNa')

    def test_invalid_existential_inside_univ_max_steps(self):
        self.invalid_tab('b', 'VxUFxSyFy', max_steps = 100)

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


class TestModelRefactorBugs(Base):

    def test_model_branch_proof_deny_antec(self):
        tab = self.tab('Denying the Antecedent')
        m = self.m()
        b = tab.open[0]
        m.read_branch(b)
        s = Atomic(0, 0)
        self.assertEqual(m.value_of(s, world=0), 'F')
        self.assertEqual(m.value_of(~s, world=0), 'T')

class TestModelAtomics(Base):

    def test_model_value_of_atomic_unassigned(self):
        s = Atomic(0, 0)
        m = self.m().finish()
        self.assertEqual(m.value_of(s), m.Meta.unassigned_value)

    def test_model_branch_no_proof_atomic(self):
        s = Atomic(0, 0)
        m = self.m()
        b = Branch()
        b += swnode(s, 0)
        m.read_branch(b)
        self.assertEqual(m.value_of(Atomic(0, 0), world=0), 'T')

class TestModelOpaques(Base):

    def test_finish_every_opaque_has_value_in_every_frame(self):
        s1, s2 = self.pp('a', 'b')
        m = self.m()
        with self.m() as m:
            m.set_opaque_value(s1, 'T', world=0)
            m.set_opaque_value(s2, 'T', world=1)
        f1 = m.frames[0]
        f2 = m.frames[1]
        self.assertIn(s2, f1.opaques)
        self.assertIn(s1, f2.opaques)

class TestModelPredication(Base):

    def test_branch_no_proof_predicated(self):
        s1 = self.p('Imn')
        m = self.m()
        b = Branch()
        b += swnode(s1, 0)
        m.read_branch(b)
        self.assertEqual(m.value_of(s1, world=0), 'T')

    def test_set_predicated_value1(self):
        s = Predicate.Identity(Constant.gen(2))
        with self.m() as m:
            m.set_value(s, 'T', world=0)
        res = m.value_of(s, world=0)
        self.assertEqual(res, 'T')

    def test_model_identity_extension_non_empty_with_sentence(self):
        s = self.p('Imn')
        with self.m() as m:
            m.set_value(s, 'T', world=0)
        interp = m.frames[0].predicates[Predicate.Identity]
        self.assertGreater(len(interp.pos), 0)
        self.assertIn((Constant(0, 0), Constant(1, 0)), interp.pos)

    def test_set_predicated_raises_free_variables(self):
        m = self.m()
        s1 = Predicated(Predicate(0,0,1), Constant(0,0))
        m.set_value(s1, 'F')
        s2 = Predicated(Predicate(0,0,1), Variable(0,0))
        with self.assertRaises(ValueError):
            m.set_predicated_value(s2, 'F')

class TestModelModalAccess(Base):

    def test_model_branch_no_proof_access(self):
        m = self.m()
        b = Branch()
        b += anode(0, 1)
        m.read_branch(b)
        self.assertIn(1, m.R[0])

    def test_model_add_access_sees(self):
        m = self.m()
        m.R.add((0,0))
        self.assertTrue(m.R.has((0,0)))

    def test_model_possibly_a_with_access_true(self):
        s1 = Atomic(0, 0)
        s2 = Operator.Possibility(s1)
        with self.m() as m:        
            m.set_value(s1, 'T', world=1)
            m.R.add((0,1))
        res = m.value_of(s2, world=0)
        self.assertEqual(res, 'T')

    def test_model_possibly_a_no_access_false(self):
        s1 = Atomic(0, 0)
        s2 = Operator.Possibility(s1)
        with self.m() as m:        
            m.set_value(s1, 'T', world=1)
        self.assertEqual(m.value_of(s2, world=0), 'F')

    def test_model_nec_a_no_access_true(self):
        s1 = Atomic(0, 0)
        s2 = Operator.Necessity(s1)
        m = self.m().finish()
        self.assertEqual(m.value_of(s2, world=0), 'T')

    def test_model_nec_a_with_access_false(self):
        s1 = Atomic(0, 0)
        s2 = Operator.Necessity(s1)
        with self.m() as m:        
            m.set_value(s1, 'T', world=0)
            m.set_value(s1, 'F', world=1)
            m.R.add((0,1))
            m.R.add((0,0))
        self.assertEqual(m.value_of(s2, world=0), 'F')

    def test_model_get_data_with_access_has_2_frames(self):
        s1 = Atomic(0, 0)
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.R.add((0,1))
        data = m.get_data()
        self.assertEqual(len(data['Frames']['values']), 2)

class TestModelQuantification(Base):

    def test_model_existence_user_pred_true(self):
        pred, x = Predicate.first(), Variable.first()
        s1, s2 = pred(Constant.first()), pred(x)
        s3 = Quantifier.Existential(x, s2)
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
        res = m.value_of(s3, world=0)
        self.assertEqual(res, 'T')

    def test_model_existense_user_pred_false(self):
        pred = Predicate(0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1, s2 = pred(m), pred(x)
        s3 = Quantified('Existential', x, s2)
        m = self.m().finish()
        res = m.value_of(s3, world=0)
        self.assertEqual(res, 'F')

    def test_model_universal_user_pred_true(self):
        pred = Predicate(0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1, s2 = pred(m), pred(x)
        s3 = Quantified('Universal', x, s2)

        with self.m() as m:
            m.set_value(s1, 'T', world=0)
        res = m.value_of(s3, world=0)
        self.assertEqual(res, 'T')

    def test_model_universal_false(self):
        s1, s2 = self.pp('VxFx', 'Fm')
        with self.m() as m:
            m.set_value(s2, 0, world=0)
        res = m.value_of(s1, world=0)
        self.assertEqual(res, 'F')

    def test_model_universal_user_pred_false(self):
        pred = Predicate(0, 0, 1)
        m = Constant(0, 0)
        n = Constant(1, 0)
        x = Variable(0, 0)
        s1, s2, s3 = (pred(p) for p in (m, x, n))
        s4 = Quantified('Universal', x, s2)
    
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s3, 'F', world=0)
        res = m.value_of(s4, world=0)
        self.assertEqual(res, 'F')

class TestFrame(Base):

    def test_difference_atomic_keys_diff(self):
        s1, s2 = self.pp('a', 'b')
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s2, 'T', world=1)
        f1, f2 = m.frames.values()
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f1)

    def test_difference_atomic_values_diff(self):
        s1 = self.p('a')
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s1, 'F', world=1)
        f1, f2 = m.frames.values()
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f1)

    def test_difference_atomic_values_equiv(self):
        s1 = self.p('a')
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s1, 'T', world=1)
        f1, f2 = m.frames.values()
        self.assertEqual(f1, f2)
        self.assertEqual(f2, f1)

    def test_difference_opaque_keys_diff(self):
        with self.m() as m:
            m.set_opaque_value(self.p('Ma'), 'T', world=0)
            m.set_opaque_value(self.p('Mb'), 'T', world=1)
        f1, f2 = m.frames.values()
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f1)

    def test_difference_opaque_values_diff(self):
        s1 = self.p('Ma')
        with self.m() as m:
            m.set_opaque_value(s1, 'T', world=0)
            m.set_opaque_value(s1, 'F', world=1)
        f1, f2 = m.frames.values()
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f1)

    def test_difference_opaque_values_equiv(self):
        with self.m() as m:
            m.set_opaque_value(self.p('Ma'), 'T', world=0)
            m.set_opaque_value(self.p('Ma'), 'T', world=1)
        f1, f2 = m.frames.values()
        self.assertEqual(f1, f2)
        self.assertEqual(f2, f1)

    def test_difference_extension_keys_diff(self):
        preds = Predicates({(0, 0, 1), (1, 0, 2)})
        s1, s2 = self.pp('Fm', 'Gmn', preds)
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s2, 'T', world=1)
        f1, f2 = m.frames.values()
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f1)

    def test_difference_extension_values_diff(self):
        s1, s2 = self.pp('Fm', 'Fn')
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s2, 'T', world=1)
        f1, f2 = m.frames.values()
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f1)

    def test_difference_extension_values_equiv(self):
        s1, s2 = self.pp('Fm', 'Fn')
        with self.m() as m:
            m.set_value(s1, 'T', world=0)
            m.set_value(s2, 'F', world=0)
            m.set_value(s1, 'T', world=1)
            m.set_value(s2, 'F', world=1)
        f1, f2 = m.frames.values()
        self.assertEqual(f1, f2)
        self.assertEqual(f2, f1)

    def test_not_equals_atomics_differ(self):
        s = self.p('a')
        with self.m() as m1:
            m1.set_value(s, 'T', world=0)
        with self.m() as m2:
            m2.set_value(s, 'F', world=0)
        f1 = m1.frames[0]
        f2 = m2.frames[0]
        self.assertNotEqual(f1, f2)

    def test_not_equals_atomics_predicates_differ(self):
        s1, s2 = self.pp('Fm', 'Gm')
        with self.m() as m1:
            m1.set_value(s1, 'T', world=0)
        with self.m() as m2:
            m2.set_value(s2, 'T', world=0)
        f1 = m1.frames[0]
        f2 = m2.frames[0]
        self.assertNotEqual(f1, f2)

    def test_not_equals_atomics_predicates_differ2(self):
        s1, s2 = self.pp('Fm', 'Gm')
        with self.m() as m1:
            m1.set_value(s1, 'T', world=0)
        with self.m() as m2:
            m2.set_value(s1, 'T', world=0)
            m2.set_value(s2, 'T', world=0)
        f1 = m1.frames[0]
        f2 = m2.frames[0]
        self.assertNotEqual(f1, f2)

    def test_not_equals_atomics_predicates_differ3(self):
        s1, s2, s3 = self.pp('Fm', 'Gm', 'Hm')
        with self.m() as m1:
            m1.set_value(s1, 'T', world=0)
            m1.set_value(s2, 'T', world=0)
        with self.m() as m2:
            m2.set_value(s1, 'T', world=0)
            m2.set_value(s3, 'T', world=0)
        f1 = m1.frames[0]
        f2 = m2.frames[0]
        self.assertNotEqual(f1, f2)

    def test_equals_self(self):
        s = self.p('a')
        with self.m() as m:
            m.set_literal_value(s, 'T', world=0)
        f = m.frames[0]
        self.assertEqual(f, f)

    def test_equals_not_impl_non_frame(self):
        s = self.p('a')
        with self.m() as m:
            m.set_value(s, 'T', world=0)
        f = m.frames[0]
        self.assertIs(NotImplemented, f.__eq__('asdf'))

    def test_data_has_identity_with_sentence(self):
        s = self.p('Imn')
        with self.m() as m:
            m.set_value(s, 'T', world=0)
        data = m.get_data()
        self.assertEqual(len(data['Frames']['values']), 1)
        fdata = data['Frames']['values'][0]['value']
        self.assertEqual(len(fdata['Predicates']['values']), 2)
        pdata = fdata['Predicates']['values'][1]
        self.assertEqual(pdata['values'][0]['input'].name, 'Identity')

class TestCounterModel(Base):

    def test_countermodel_to_false1(self):
        arg = self.parg('b', 'a')
        s1, = arg.premises
        with self.m() as m:
            m.set_value(s1, 'F')
            m.set_value(arg.conclusion, 'T')
        self.assertFalse(m.is_countermodel_to(arg))

class TestModelErrors(Base):

    def test_not_impl_various(self):
        s1 = self.p('Aab')
        m = self.m()
        with self.assertRaises(NotImplementedError):
            m.set_literal_value(s1, 'T')

    def test_value_error_various(self):
        s1, s2 = self.pp('a', 'Fm')
        m = self.m()
        m.set_opaque_value(s1, 'T')
        with self.assertRaises(ModelValueError):
            m.set_opaque_value(s1, 'F')
        m = self.m()
        m.set_atomic_value(s1, 'T')
        with self.assertRaises(ModelValueError):
            m.set_atomic_value(s1, 'F')
        m.set_predicated_value(s2, 'T')
        with self.assertRaises(ModelValueError):
            m.set_predicated_value(s2, 'F')

class TestBranchables(Base):

    branchings = dict(
        Biconditional=1,
        BiconditionalNegated=1,
        Conditional=1,
        ConjunctionNegated=1,
        Disjunction=1,
        MaterialBiconditional=1,
        MaterialBiconditionalNegated=1,
        MaterialConditional=1,)

    @classmethod
    def gentest(cls):
        for rulecls in cls.logic.Rules.all():
            exp = cls.branchings.get(rulecls.name, 0)
            name = f'test_{rulecls.name}_branching_is_{exp}'
            yield name, cls.maketest('assertEqual', rulecls.branching, exp)

class TestSystem(Base):

    def test_branch_complexity_hashable_none_if_no_sentence(self):
        n = Node({})
        self.assertIs(None, K.System.branching_complexity_hashable(n))

    def test_branch_complexity_0_if_no_sentence(self):
        tab = Tableau(self.logic)
        n = Node({})
        self.assertEqual(0, K.System.branching_complexity(n, tab.rules))

    def test_abstract_default_node_rule(self):
        class Impl(K.System.DefaultNodeRule): pass
        with self.assertRaises(TypeError):
            Impl(Tableau())
        rule = rules.NoopRule(Tableau())
        with self.assertRaises(NotImplementedError):
            Impl._get_sw_targets(rule, Node({}), Branch())

    def test_abstract_operator_node_rule(self):
        class Impl(K.System.OperatorNodeRule): pass
        with self.assertRaises(TypeError):
            Impl(Tableau())
        rule = rules.NoopRule(Tableau())
        with self.assertRaises(NotImplementedError):
            Impl._get_sw_targets(rule, Node({}), Branch())

    def test_notimpl_coverage(self):
        rule = rules.NoopRule(Tableau())
        with self.assertRaises(NotImplementedError):
            K.System.DefaultNodeRule._get_sw_targets(rule, self.p('a'), 0)
        with self.assertRaises(NotImplementedError):
            K.System.OperatorNodeRule._get_sw_targets(rule, self.p('a'), 0)
