from ..utils import BaseCase
from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

class Base(BaseCase):
    logic = 'K'

class TestRules(Base, autorules=True): pass
class TestAutoArgs(Base, autoargs=True): pass

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

class TestRuleAttrs(Base):
    def test_rules_modal(self):
        for rcls in self.logic.Rules.all():
            self.assertIs(rcls.modal, True)

class TestClosureRules(Base):

    def test_ContradictionClosure(self):
        self.valid_tab('EFQ')

    def test_SelfIdentityClosure(self):
        self.valid_tab('Self Identity 1')

    def test_NonExistenceClosure(self):
        self.valid_tab('b', 'NJm')

class TestOperatorRules(Base):

    def test_Assertion(self):
        self.valid_tab('Assertion Elimination 1')
        self.valid_tab('Assertion Elimination 2')

    def test_Conjunction(self):
        self.valid_tab('Conjunction Introduction')

    def test_Disjunction(self):
        rule, tab = self.rule_eg('DisjunctionNegated', step = False)
        s = tab[0][0]['sentence']
        self.assertEqual(s.operator, Operator.Negation)

        self.valid_tab('Addition')
        self.valid_tab('LEM')
        self.valid_tab('Disjunctive Syllogism')
        self.valid_tab('Disjunctive Syllogism 2')

    def test_MaterialConditional(self):
        self.valid_tab('MMP')
        self.valid_tab('MMT')

    def test_MaterialBiconditional(self):
        self.valid_tab('Material Biconditional Elimination 1')
        self.valid_tab('Material Biconditional Introduction 1')

    def test_Conditional(self):
        self.valid_tab('MP')
        self.valid_tab('MT')
        self.invalid_tab('Denying the Antecedent')

class TestModalOperatorRules(Base):

    def test_Necessity(self):
        self.invalid_tab('Necessity Elimination')

    def test_Possibility(self):
        rule, tab = self.rule_eg('Possibility', step = False)
        node = tab[0][0]
        self.assertEqual(node['world'], 0)

    def test_modal_transformation(self):
        self.valid_tab('Modal Transformation 2')

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc', ('LCaMNb', 'Ma'))

    def test_Arguments_2(self):
        self.valid_tab('Necessity Distribution 1')
        self.invalid_tab('S4 Conditional Inference 2')

class TestQuantifierRules(Base):

    def test_Existential(self):
        rule, tab = self.rule_eg('Existential', step = False)
        node = tab[0][0]
        self.assertEqual(node['sentence'].quantifier, Quantifier.Existential)

    def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
        self.valid_tab('b', 'VxKFxKaNa')

    def test_invalid_existential_inside_univ_max_steps(self):
        self.invalid_tab('b', 'VxUFxSyFy', max_steps = 100)

class TestIdentityRules(Base):

    def test_regresion(self):
        rule, tab = self.rule_eg('IdentityIndiscernability')
        self.valid_tab('Identity Indiscernability 1')
        self.valid_tab('Identity Indiscernability 2')

    def test_IdentityIndiscernability(self):
        rule, tab = self.rule_eg('IdentityIndiscernability')
        b = tab.branch().extend((
            {'sentence': self.p('Imm'), 'world': 0},
            {'sentence': self.p('Fs'),  'world': 0},
        ))
        self.assertFalse(rule.target(b))

class TestModelRefactorBugs(Base):

    def test_model_branch_proof_deny_antec(self):
        tab = self.tab('Denying the Antecedent')
        model = self.m()
        branch = tab.open[0]
        model.read_branch(branch)
        s = Atomic(0, 0)
        self.assertEqual(model.value_of(s, world=0), 'F')
        self.assertEqual(model.value_of(s.negate(), world=0), 'T')

class TestModelAtomics(Base):

    def test_model_value_of_atomic_unassigned(self):
        model = self.m()
        s = Atomic(0, 0)
        res = model.value_of_atomic(s)
        self.assertEqual(res, model.unassigned_value)

    def test_model_branch_no_proof_atomic(self):
        model = self.m()
        branch = Branch()
        branch.append({'sentence': Atomic(0, 0), 'world': 0})
        model.read_branch(branch)
        self.assertEqual(model.value_of(Atomic(0, 0), world=0), 'T')

class TestModelOpaques(Base):

    def test_finish_every_opaque_has_value_in_every_frame(self):
        s1, s2 = self.pp('a', 'b')
        model = self.m()
        model.set_opaque_value(s1, 'T', world=0)
        model.set_opaque_value(s2, 'T', world=1)
        model.finish()
        f1 = model.frames[0]
        f2 = model.frames[1]
        self.assertIn(s2, f1.opaques)
        self.assertIn(s1, f2.opaques)

class TestModelPredication(Base):

    def test_branch_no_proof_predicated(self):
        model = self.m()
        branch = Branch()
        s1 = self.p('Imn')
        branch.append({'sentence': s1, 'world': 0})
        model.read_branch(branch)
        self.assertEqual(model.value_of(s1, world=0), 'T')

    def test_set_predicated_value1(self):
        model = self.m()
        s = Predicate.System.Identity(tuple(Constant.gen(2)))
        model.set_predicated_value(s, 'T', world=0)
        res = model.value_of(s, world=0)
        self.assertEqual(res, 'T')

    def test_get_extension_adds_predicate_to_predicates(self):
        # coverage
        s1 = self.p('Fm')
        model = self.m()
        res = model.get_extension(s1.predicate)
        self.assertEqual(len(res), 0)
        self.assertIn(s1.predicate, model.predicates)

    def test_model_identity_extension_non_empty_with_sentence(self):
        s = self.p('Imn')
        model = self.m()
        model.set_predicated_value(s, 'T', world=0)
        extension = model.get_extension(Predicate.Identity, world=0)
        self.assertGreater(len(extension), 0)
        self.assertIn((Constant(0, 0), Constant(1, 0)), extension)

class TestModelModalAccess(Base):

    def test_model_branch_no_proof_access(self):
        model = self.m()
        branch = Branch()
        branch.append({'world1': 0, 'world2': 1})
        model.read_branch(branch)
        self.assertIn(1, model.R[0])

    def test_model_add_access_sees(self):
        model = self.m()
        model.R.add((0,0))
        self.assertTrue(model.R.has((0,0)))

    def test_model_possibly_a_with_access_true(self):
        model = self.m()
        a = Atomic(0, 0)
        model.R.add((0,1))
        model.set_atomic_value(a, 'T', world=1)
        res = model.value_of(Operator.Possibility(a), world=0)
        self.assertEqual(res, 'T')

    def test_model_possibly_a_no_access_false(self):
        model = self.m()
        a = Atomic(0, 0)
        model.set_atomic_value(a, 'T', world=1)
        res = model.value_of(Operated('Possibility', a), world=0)
        self.assertEqual(res, 'F')

    def test_model_nec_a_no_access_true(self):
        model = self.m()
        a = Atomic(0, 0)
        res = model.value_of(Operated('Necessity', a), world=0)
        self.assertEqual(res, 'T')

    def test_model_nec_a_with_access_false(self):
        model = self.m()
        a = Atomic(0, 0)
        model.set_atomic_value(a, 'T', world=0)
        model.set_atomic_value(a, 'F', world=1)
        model.R.add((0,1))
        model.R.add((0,0))
        res = model.value_of(Operated('Necessity', a), world=0)
        self.assertEqual(res, 'F')

    def test_model_get_data_with_access_has_2_frames(self):
        model = self.m()
        model.set_literal_value(self.p('a'), 'T', world=0)
        model.R.add((0,1))
        model.finish()
        data = model.get_data()
        self.assertEqual(len(data['Frames']['values']), 2)

class TestModelQuantification(Base):

    def test_model_existence_user_pred_true(self):
        pred, x = Predicate.first(), Variable.first()
        s1, s2 = pred(Constant.first()), pred(x)
        s3 = Quantifier.Existential(x, s2)
        model = self.m()
        model.set_predicated_value(s1, 'T', world=0)
        res = model.value_of(s3, world=0)
        self.assertEqual(res, 'T')

    def test_model_existense_user_pred_false(self):
        pred = Predicate(0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1, s2 = pred(m), pred(x)
        s3 = Quantified('Existential', x, s2)

        model = self.m()
        res = model.value_of(s3, world=0)
        self.assertEqual(res, 'F')

    def test_model_universal_user_pred_true(self):
        pred = Predicate(0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1, s2 = pred(m), pred(x)
        s3 = Quantified('Universal', x, s2)

        model = self.m()
        model.set_predicated_value(s1, 'T', world=0)
        res = model.value_of(s3, world=0)
        self.assertEqual(res, 'T')

    def test_model_universal_false(self):
        s1, s2 = self.pp('VxFx', 'Fm')
        model = self.m()
        model.set_predicated_value(s2, 0, world=0)
        res = model.value_of(s1, world=0)
        self.assertEqual(res, 'F')

    def test_model_universal_user_pred_false(self):
        pred = Predicate(0, 0, 1)
        m = Constant(0, 0)
        n = Constant(1, 0)
        x = Variable(0, 0)
        s1, s2, s3 = (pred(p) for p in (m, x, n))
        s4 = Quantified('Universal', x, s2)
    
        model = self.m()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s3, 'F', world=0)
        res = model.value_of(s4, world=0)
        self.assertEqual(res, 'F')

class TestFrame(Base):

    def test_difference_atomic_keys_diff(self):
        model = self.m()
        model.set_literal_value(self.p('a'), 'T', world=0)
        model.set_literal_value(self.p('b'), 'T', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertFalse(frame_a.is_equivalent_to(frame_b))
        self.assertFalse(frame_b.is_equivalent_to(frame_a))

    def test_difference_atomic_values_diff(self):
        model = self.m()
        s1 = self.p('a')
        model.set_literal_value(s1, 'T', world=0)
        model.set_literal_value(s1, 'F', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertFalse(frame_a.is_equivalent_to(frame_b))
        self.assertFalse(frame_b.is_equivalent_to(frame_a))

    def test_difference_atomic_values_equiv(self):
        model = self.m()
        s1 = self.p('a')
        model.set_literal_value(s1, 'T', world=0)
        model.set_literal_value(s1, 'T', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertTrue(frame_a.is_equivalent_to(frame_b))
        self.assertTrue(frame_b.is_equivalent_to(frame_a))

    def test_difference_opaque_keys_diff(self):
        model = self.m()
        model.set_opaque_value(self.p('Ma'), 'T', world=0)
        model.set_opaque_value(self.p('Mb'), 'T', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertFalse(frame_a.is_equivalent_to(frame_b))
        self.assertFalse(frame_b.is_equivalent_to(frame_a))

    def test_difference_opaque_values_diff(self):
        s1 = self.p('Ma')
        model = self.m()
        model.set_opaque_value(s1, 'T', world=0)
        model.set_opaque_value(s1, 'F', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertFalse(frame_a.is_equivalent_to(frame_b))
        self.assertFalse(frame_b.is_equivalent_to(frame_a))

    def test_difference_opaque_values_equiv(self):
        model = self.m()
        model.set_opaque_value(self.p('Ma'), 'T', world=0)
        model.set_opaque_value(self.p('Ma'), 'T', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertTrue(frame_a.is_equivalent_to(frame_b))
        self.assertTrue(frame_b.is_equivalent_to(frame_a))

    def test_difference_extension_keys_diff(self):
        preds = Predicates({(0, 0, 1), (1, 0, 2)})
        s1, s2 = self.pp('Fm', 'Gmn', preds)
        model = self.m()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s2, 'T', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertFalse(frame_a.is_equivalent_to(frame_b))
        self.assertFalse(frame_b.is_equivalent_to(frame_a))

    def test_difference_extension_values_diff(self):
        s1 = self.p('Fm')
        s2 = self.p('Fn')
        model = self.m()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s2, 'T', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertFalse(frame_a.is_equivalent_to(frame_b))
        self.assertFalse(frame_b.is_equivalent_to(frame_a))

    def test_difference_extension_values_equiv(self):
        s1 = self.p('Fm')
        s2 = self.p('Fn')
        model = self.m()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s2, 'F', world=0)
        model.set_predicated_value(s1, 'T', world=1)
        model.set_predicated_value(s2, 'F', world=1)
        frame_a = model.frames[0]
        frame_b = model.frames[1]
        self.assertTrue(frame_a.is_equivalent_to(frame_b))
        self.assertTrue(frame_b.is_equivalent_to(frame_a))

    def test_not_equals(self):
        s = self.p('a')
        model1 = self.m()
        model2 = self.m()
        model1.set_literal_value(s, 'T', world=0)
        model2.set_literal_value(s, 'F', world=0)
        f1 = model1.frames[0]
        f2 = model2.frames[0]
        self.assertNotEqual(f1, f2)

    def test_not_equals(self):
        s = self.p('a')
        model1 = self.m()
        model2 = self.m()
        model1.set_literal_value(s, 'T', world=0)
        model2.set_literal_value(s, 'T', world=0)
        f1 = model1.frames[0]
        f2 = model2.frames[0]
        self.assertEqual(f1, f2)

    def test_ordering(self):
        s = self.p('a')
        model = self.m()
        model.set_literal_value(s, 'T', world=0)
        model.set_literal_value(s, 'F', world=1)
        f1 = model.frames[0]
        f2 = model.frames[1]
        self.assertGreater(f2, f1)
        self.assertLess(f1, f2)
        self.assertGreaterEqual(f2, f1)
        self.assertLessEqual(f1, f2)

    def test_data_has_identity_with_sentence(self):
        s = self.p('Imn')
        model = self.m()
        model.set_predicated_value(s, 'T', world=0)
        model.finish()
        data = model.get_data()
        self.assertEqual(len(data['Frames']['values']), 1)
        fdata = data['Frames']['values'][0]['value']
        self.assertEqual(len(fdata['Predicates']['values']), 2)
        pdata = fdata['Predicates']['values'][1]
        self.assertEqual(pdata['values'][0]['input'].name, 'Identity')

class TestCounterModel(Base):

    def test_countermodel_to_false1(self):
        arg = self.parg('b', 'a')
        s1, = arg.premises
        model = self.m()
        model.set_literal_value(s1, 'F')
        model.set_literal_value(arg.conclusion, 'T')
        self.assertFalse(model.is_countermodel_to(arg))

class TestModelErrors(Base):

    def test_not_impl_various(self):
        s1 = self.p('Aab')
        model = self.m()
        with self.assertRaises(NotImplementedError):
            model.set_literal_value(s1, 'T')

    def test_value_error_various(self):
        s1, s2 = self.pp('a', 'Fm')
        model = self.m()
        model.set_opaque_value(s1, 'T')
        with self.assertRaises(ModelValueError):
            model.set_opaque_value(s1, 'F')
        model = self.m()
        model.set_atomic_value(s1, 'T')
        with self.assertRaises(ModelValueError):
            model.set_atomic_value(s1, 'F')
        model.set_predicated_value(s2, 'T')
        with self.assertRaises(ModelValueError):
            model.set_predicated_value(s2, 'F')

class TestBranchables(Base):

    exp = dict(
        Assertion=0,
        AssertionNegated=0,
        Biconditional=1,
        BiconditionalNegated=1,
        Conditional=1,
        ConditionalNegated=0,
        Conjunction=0,
        ConjunctionNegated=1,
        ContradictionClosure=0,
        Disjunction=1,
        DisjunctionNegated=0,
        DoubleNegation=0,
        Existential=0,
        ExistentialNegated=0,
        IdentityIndiscernability=0,
        MaterialBiconditional=1,
        MaterialBiconditionalNegated=1,
        MaterialConditional=1,
        MaterialConditionalNegated=0,
        Necessity=0,
        NecessityNegated=0,
        NonExistenceClosure=0,
        Possibility=0,
        PossibilityNegated=0,
        SelfIdentityClosure=0,
        Universal=0,
        UniversalNegated=0)

    def test_known_branchable_values(self):
        for rulecls in self.logic.Rules.all():
            self.assertEqual(rulecls.branching, self.exp[rulecls.name])
