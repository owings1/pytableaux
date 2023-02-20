from .. import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

A = Atomic.first()

class Base(BaseCase):
    logic = 'FDE'

class TestArguments(Base):

    def test_DeMorgan(self):
        self.valid_tab('DeMorgan 1')
        self.valid_tab('DeMorgan 2')
        self.valid_tab('DeMorgan 3')
        self.valid_tab('DeMorgan 4')

class TestClosure(Base):

    def test_DesignationClosure(self):
        self.rule_eg('DesignationClosure')

class TestOperators(Base):

    def test_Negation(self):
        self.rule_eg('DoubleNegationDesignated')
        self.rule_eg('DoubleNegationUndesignated')

    def test_Assertion(self):
        o = Operator.Assertion
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')
        # ¬ ○ A  ⊢  ¬ A
        Operator.Negation(Operator.Assertion(A))
        Operator.Negation(A)
        self.valid_tab('Na', 'NTa')

    def test_Conjunction(self):
        o = Operator.Conjunction
        rtd = self.rule_eg(f'{o.name}Designated')
        rtu = self.rule_eg(f'{o.name}Undesignated')
        rtnd = self.rule_eg(f'{o.name}NegatedDesignated')
        rtnu = self.rule_eg(f'{o.name}NegatedUndesignated')

        self.invalid_tab('LNC')

        n = rtnd[1].history[0].target.node
        s: Operated = n['sentence']
        self.assertEqual(
            (s.operator, s.lhs.operator, n['designated']),
            (Operator.Negation, Operator.Conjunction, True))

    def test_Disjunction(self):
        o = Operator.Disjunction
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')
        self.valid_tab('Addition')
        self.invalid_tab('LEM')

    def test_MaterialConditional(self):
        o = Operator.MaterialConditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_MaterialBiconditional(self):
        o = Operator.MaterialBiconditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')
        self.invalid_tab('Material Biconditional Elimination 3')

    def test_Conditional(self):
        o = Operator.Conditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_Biconditional(self):
        o = Operator.Biconditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')


class TestQuantifiers(Base):

    def test_Existential(self):
        q = Quantifier.Existential
        rtd = self.rule_eg(f'{q.name}Designated')
        rtu = self.rule_eg(f'{q.name}Undesignated')
        rtnd = self.rule_eg(f'{q.name}NegatedDesignated')
        rtnu = self.rule_eg(f'{q.name}NegatedUndesignated')

        b = rtu[1][0]
        self.assertTrue(b.has(
            {'sentence': Quantified.first(q), 'designated': False}))

    def test_Universal(self):
        q = Quantifier.Universal
        self.rule_eg(f'{q.name}Designated')
        self.rule_eg(f'{q.name}Undesignated')
        self.rule_eg(f'{q.name}NegatedDesignated')
        self.rule_eg(f'{q.name}NegatedUndesignated')

    def test_arguments(self):
        self.valid_tab('Quantifier Interdefinability 4')
        self.invalid_tab('Universal from Existential')

    def test_invalid_existential_inside_univ_max_steps(self):
        tab = self.invalid_tab('b', 'VxUFxSyFy', max_steps=100, is_build_models=True)
        self.assertLess(len(tab.history), 100)

class TestBranchingComplexity(Base):

    def nodecase(s, des = False):
        def wrap(fn):
            def testfn(self: Base):
                tab = self.tab()
                tab.branch().add({'sentence': self.p(s), 'designated': des})
                node = tab[0][0]
                fn(self, tab[0][0], node['sentence'], tab)
            return testfn
        return wrap

    @nodecase('a')
    def test_branching_complexity_undes_0_1(self, node, s: Sentence, tab: Tableau):
        self.assertEqual(tab.branching_complexity(node), 0)

    @nodecase('Kab')
    def test_branching_complexity_undes_1_1(self, node, s: Sentence, tab: Tableau):
        self.assertEqual(tab.branching_complexity(node), 1)

    @nodecase('NAaNKbc')
    def test_branching_complexity_undes_1_2(self, node, s: Sentence, tab: Tableau):
        self.assertEqual(s.operators, (
            Operator.Negation, Operator.Disjunction, Operator.Negation, Operator.Conjunction))
        self.assertEqual(tab.branching_complexity(node), 1)

    @nodecase('NAab')
    def test_branching_complexity_undes_1_3(self, node, s: Sentence, tab: Tableau):
        self.assertEqual(s.operators, (Operator.Negation, Operator.Disjunction))
        self.assertEqual(tab.branching_complexity(node), 1)

    @nodecase('KaKab')
    def test_branching_complexity_undes_2_1(self, node, s: Sentence, tab: Tableau):
        self.assertEqual(s.operators, ('Conjunction', 'Conjunction'))
        self.assertEqual(tab.branching_complexity(node), 2)


class TestModels(Base):

    def mb(self, *nitems):
        b = Branch()
        for s, d in nitems:
            b.add(sdnode(self.p(s), d))
        m = self.Model()
        m.read_branch(b)
        return (m,b)

    def test_countermodels(self):
        self.cm('LEM')
        m = self.cm('LNC')
        self.assertEqual(m.value_of(Atomic.first()), 'B')

    def test_model_a_thus_b_is_countermodel_to_false(self):
        arg = self.parg('b', 'a')
        model = self.m()
        model.set_literal_value(arg.premises[0], 'F')
        model.set_literal_value(arg.conclusion, 'F')
        assert not model.is_countermodel_to(arg)

    def test_model_b_value_atomic_branch(self):
        s1 = self.p('a')
        m, b = self.mb(('a', True), ('Na', True))
        self.assertEqual(m.value_of(s1), 'B')

    def test_model_univ_t_value_branch(self):
        s1, s2 = self.pp('Fm', 'VxFx')
        m,b = self.mb((s1, True))
        self.assertEqual(m.value_of(s2), 'T')

    def test_model_exist_b_value_branch(self):
        s1, s2, s3 = self.pp('Fm', 'Fn', 'SxFx')
        m,b = self.mb(
            (s1, True),
            (s1.negate(), True),
            (s2, False),
            (s2.negate(), False))
        self.assertEqual(m.value_of(s3), 'B')

    def test_model_necessity_opaque_des_value_branch(self):
        s1 = self.p('La')
        b = Branch().add({'sentence': s1, 'designated': True})
        m = self.Model()
        m.read_branch(b)
        self.assertIn(m.value_of(s1), ('B', 'T'))

    def test_model_necessity_opaque_b_value_branch(self):
        s1 = self.p('La')
        b = Branch().extend((
            sdnode(s1, True),
            sdnode(s1.negate(), True)))
        m = self.Model()
        m.read_branch(b)
        self.assertEqual(m.value_of(s1), 'B')

    def test_model_atomic_undes_value_branch(self):
        s1 = self.p('a')
        b = Branch().add({'sentence': s1, 'designated': False})
        m = self.Model()
        m.read_branch(b)
        self.assertIn(m.value_of(s1), ('F', 'N'))

    def test_model_atomic_t_value_branch(self):
        branch = Branch()
        s = self.p('a')
        branch.extend([
            sdnode(s, True),
            sdnode(s.negate(), False)])
        m = self.Model()
        m.read_branch(branch)
        self.assertEqual(m.value_of(s), 'T')

    def test_model_atomic_f_value_branch(self):
        branch = Branch()
        s = self.p('a')
        branch.extend([
            sdnode(s, False),
            sdnode(s.negate(), True)])
        m = self.Model()
        m.read_branch(branch)
        self.assertEqual(m.value_of(s), 'F')

    def test_model_get_data_various(self):
        s1 = self.p('a')
        s2 = self.p('Imn')
        model = self.m()
        model.set_literal_value(s1, 'B')
        model.set_literal_value(s2, 'F')
        res = model.get_data()
        self.assertIn('Atomics', res)

    def test_model_value_of_atomic_unassigned(self):
        s = self.p('a')
        model = self.m()
        res = model.value_of(s)
        self.assertEqual(res, model.unassigned_value)

    def test_model_value_of_opaque_unassigned(self):
        s = self.p('La')
        model = self.m()
        res = model.value_of(s)
        self.assertEqual(res, model.unassigned_value)

    def test_model_value_error_various(self):
        s1 = self.p('La')
        s2 = self.p('a')
        s3 = self.p('Imn')
        model = self.m()
        model.set_opaque_value(s1, 'T')
        with self.assertRaises(ModelValueError):
            model.set_opaque_value(s1, 'B')
        model = self.m()
        model.set_atomic_value(s2, 'T')
        with self.assertRaises(ModelValueError):
            model.set_atomic_value(s2, 'B')
        model = self.m()
        model.set_predicated_value(s3, 'T')
        with self.assertRaises(ModelValueError):
            model.set_predicated_value(s3, 'N')
        model = self.m()
        model.set_predicated_value(s3, 'B')
        with self.assertRaises(ModelValueError):
            model.set_predicated_value(s3, 'T')
        model = self.m()
        model.set_predicated_value(s3, 'B')
        with self.assertRaises(ModelValueError):
            model.set_predicated_value(s3, 'F')
        model = self.m()
        model.set_predicated_value(s3, 'F')
        with self.assertRaises(ModelValueError):
            model.set_predicated_value(s3, 'N')
        model = self.m()
        with self.assertRaises(ValueError):
            model.truth_function('Foomunction', 'F')

    def test_error_various(self):
        s = self.p('Aab')
        with self.assertRaises(NotImplementedError):
            self.m().set_literal_value(s, 'T')
        with self.assertRaises(TypeError):
            self.m().value_of_quantified(s)

    def test_model_read_branch_with_negated_opaque_then_faithful(self):
        arg = self.parg('a', 'NLa', 'b')
        proof = Tableau(self.logic, arg, is_build_models=True)
        proof.build()
        model = proof[0].model
        self.assertEqual(model.value_of(self.p('a')), 'F')
        self.assertEqual(model.value_of(self.p('La')), 'F')
        self.assertEqual(model.value_of(self.p('NLa')), 'T')
        self.assertTrue(model.is_countermodel_to(arg))

    def test_observed_value_of_universal_with_diamond_min_arg_is_an_empty_sequence(self):
        arg = self.parg('b', 'VxUFxSyMFy')
        proof = Tableau(self.logic, arg, is_build_models=False, max_steps=100).build()
        self.assertTrue(proof.invalid)
        branch = proof[-1]
        model = self.m()
        model.read_branch(branch)
        s1 = arg.premises[0]
        self.assertIn(model.value_of(s1), model.designated_values)

    def test_observed_as_above_reconstruct1(self):
        # solution was to add all constants in set_opaque_value
        s1, s2, s3, s4, s5, s6 = self.pp(
            'MFs',          # designated
            'MFo',          # designated
            'MFn',          # designated
            'b',            # undesignated
            'SyMFy',        # designated
            'VxUFxSyMFy',   # designated
        )
        model = self.m()
        model.set_opaque_value(s1, 'T')
        model.set_opaque_value(s2, 'T')
        model.set_opaque_value(s3, 'T')
        model.set_literal_value(s4, 'F')
        self.assertEqual(model.value_of(s3), 'T')
        self.assertIn(s3, model.opaques)
        self.assertIn(model.value_of(s5), model.designated_values)