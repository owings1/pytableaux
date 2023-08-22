from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

A = Atomic.first()

class Base(BaseCase):
    logic = 'FDE'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNBT',
        Negation = 'TNBF',
        Conjunction = 'FFFFFNNNFNBBFNBT',
        Disjunction = 'FNBTNNBTBBBTTTTT',
        MaterialConditional = 'TTTTNNBTBBBTFNBT',
        MaterialBiconditional = 'TNBFNNBNBBBBFNBT',
        Conditional = 'TTTTNNBTBBBTFNBT',
        Biconditional = 'TNBFNNBNBBBBFNBT',
    )

class TestOperators(Base):

    def test_Conjunction(self):
        o = Operator.Conjunction
        rtnd = self.rule_eg(f'{o.name}NegatedDesignated')

        n = rtnd[1].history[0].target.node
        s: Operated = n['sentence']
        self.assertEqual(
            (s.operator, s.lhs.operator, n['designated']),
            (Operator.Negation, Operator.Conjunction, True))

class TestQuantifiers(Base):

    def test_Existential(self):
        q = Quantifier.Existential
        rtu = self.rule_eg(f'{q.name}Undesignated')

        b = rtu[1][0]
        self.assertTrue(b.has(sdnode(Quantified.first(q), False)))

    def test_invalid_existential_inside_univ_max_steps(self):
        tab = self.invalid_tab('b', 'VxUFxSyFy', max_steps=100, is_build_models=True)
        self.assertLess(len(tab.history), 100)

class TestBranchingComplexity(Base):

    def nodecase(s, des = False):
        def wrap(fn):
            def testfn(self: Base):
                tab = self.tab()
                tab.branch().append({'sentence': self.p(s), 'designated': des})
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
            b.append(sdnode(self.p(s), d))
        m = self.m()
        m.read_branch(b)
        return (m,b)

    def test_countermodels(self):
        self.cm('LEM')
        m = self.cm('LNC')
        self.assertEqual(m.value_of(Atomic.first()), 'B')

    def test_model_a_thus_b_is_countermodel_to_false(self):
        arg = self.parg('b', 'a')
        with self.m() as m:
            m.set_literal_value(arg.premises[0], 'F')
            m.set_literal_value(arg.conclusion, 'F')
        assert not m.is_countermodel_to(arg)

    def test_model_b_value_atomic_branch(self):
        s1 = self.p('a')
        m, b = self.mb(('a', True), ('Na', True))
        self.assertEqual(m.value_of(s1), 'B')

    def test_model_univ_t_value_branch(self):
        s1, s2 = self.pp('Fm', 'VxFx')
        m, b = self.mb((s1, True))
        self.assertEqual(m.value_of(s2), 'T')

    def test_model_exist_b_value_branch(self):
        s1, s2, s3 = self.pp('Fm', 'Fn', 'SxFx')
        m, b = self.mb(
            (s1, True),
            (~s1, True),
            (s2, False),
            (~s2, False))
        self.assertEqual(m.value_of(s3), 'B')

    def test_model_necessity_opaque_des_value_branch(self):
        s1 = self.p('La')
        m, b = self.mb((s1, True))
        self.assertIn(m.value_of(s1), ('B', 'T'))

    def test_model_necessity_opaque_b_value_branch(self):
        s1 = self.p('La')
        m, b = self.mb((s1, True), (~s1, True))
        self.assertEqual(m.value_of(s1), 'B')

    def test_model_atomic_undes_value_branch(self):
        s1 = self.p('a')
        m, b = self.mb((s1, False))
        self.assertIn(m.value_of(s1), ('F', 'N'))

    def test_model_atomic_t_value_branch(self):
        s = self.p('a')
        m, b = self.mb((s, True), (~s, False))
        self.assertEqual(m.value_of(s), 'T')

    def test_model_atomic_f_value_branch(self):
        s = self.p('a')
        m, b = self.mb((s, False), (~s, True))
        self.assertEqual(m.value_of(s), 'F')

    def test_model_get_data_various(self):
        s1, s2 = self.pp('a', 'Imn')
        with self.m() as m:
            m.set_literal_value(s1, 'B')
            m.set_literal_value(s2, 'F')
        res = m.get_data()
        self.assertIn('Atomics', res)

    def test_model_value_of_atomic_unassigned(self):
        s = self.p('a')
        m = self.m()
        m.finish()
        res = m.value_of(s)
        self.assertEqual(res, m.unassigned_value)

    def test_model_value_of_opaque_unassigned(self):
        s = self.p('La')
        m = self.m()
        m.finish()
        res = m.value_of(s)
        self.assertEqual(res, m.unassigned_value)

    def test_model_value_error_various(self):
        s1, s2, s3 = self.pp('La', 'a', 'Imn')
        m = self.m()
        m.set_opaque_value(s1, 'T')
        with self.assertRaises(ModelValueError):
            m.set_opaque_value(s1, 'B')
        m = self.m()
        m.set_atomic_value(s2, 'T')
        with self.assertRaises(ModelValueError):
            m.set_atomic_value(s2, 'B')
        m = self.m()
        m.set_predicated_value(s3, 'T')
        with self.assertRaises(ModelValueError):
            m.set_predicated_value(s3, 'N')
        m = self.m()
        m.set_predicated_value(s3, 'B')
        with self.assertRaises(ModelValueError):
            m.set_predicated_value(s3, 'T')
        m = self.m()
        m.set_predicated_value(s3, 'B')
        with self.assertRaises(ModelValueError):
            m.set_predicated_value(s3, 'F')
        m = self.m()
        m.set_predicated_value(s3, 'F')
        with self.assertRaises(ModelValueError):
            m.set_predicated_value(s3, 'N')
        m = self.m()
        with self.assertRaises(ValueError):
            m.truth_function('Foomunction', 'F')

    def test_error_various(self):
        s = self.p('Aab')
        with self.assertRaises(NotImplementedError):
            self.m().set_literal_value(s, 'T')
        with self.assertRaises(TypeError):
            self.m().value_of_quantified(s)

    def test_model_read_branch_with_negated_opaque_then_faithful(self):
        tab = self.tab('a', 'NLa', 'b')
        m = tab[0].model
        s1, s2, s3 = self.pp('a', 'La', 'NLa')
        self.assertEqual(m.value_of(s1), 'F')
        self.assertEqual(m.value_of(s2), 'F')
        self.assertEqual(m.value_of(s3), 'T')
        self.assertTrue(m.is_countermodel_to(tab.argument))

    def test_observed_value_of_universal_with_diamond_min_arg_is_an_empty_sequence(self):
        arg = self.parg('b', 'VxUFxSyMFy')
        tab = self.tab(arg, is_build_models=False, max_steps=100)
        self.assertTrue(tab.invalid)
        b = tab[-1]
        m = self.m()
        m.read_branch(b)
        s1 = arg.premises[0]
        self.assertIn(m.value_of(s1), m.designated_values)

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
        with self.m() as m:
            m.set_opaque_value(s1, 'T')
            m.set_opaque_value(s2, 'T')
            m.set_opaque_value(s3, 'T')
            m.set_literal_value(s4, 'F')
        self.assertEqual(m.value_of(s3), 'T')
        self.assertIn(s3, m.opaques)
        self.assertIn(m.value_of(s5), m.designated_values)

class TestBranchables(Base):
    exp = dict(
        AssertionDesignated=0,
        AssertionNegatedDesignated=0,
        AssertionNegatedUndesignated=0,
        AssertionUndesignated=0,
        BiconditionalDesignated=1,
        BiconditionalNegatedDesignated=1,
        BiconditionalNegatedUndesignated=1,
        BiconditionalUndesignated=1,
        ConditionalDesignated=1,
        ConditionalNegatedDesignated=0,
        ConditionalNegatedUndesignated=1,
        ConditionalUndesignated=0,
        ConjunctionDesignated=0,
        ConjunctionNegatedDesignated=1,
        ConjunctionNegatedUndesignated=0,
        ConjunctionUndesignated=1,
        DesignationClosure=0,
        DisjunctionDesignated=1,
        DisjunctionNegatedDesignated=0,
        DisjunctionNegatedUndesignated=1,
        DisjunctionUndesignated=0,
        DoubleNegationDesignated=0,
        DoubleNegationUndesignated=0,
        ExistentialDesignated=0,
        ExistentialNegatedDesignated=0,
        ExistentialNegatedUndesignated=0,
        ExistentialUndesignated=0,
        MaterialBiconditionalDesignated=1,
        MaterialBiconditionalNegatedDesignated=1,
        MaterialBiconditionalNegatedUndesignated=1,
        MaterialBiconditionalUndesignated=1,
        MaterialConditionalDesignated=1,
        MaterialConditionalNegatedDesignated=0,
        MaterialConditionalNegatedUndesignated=1,
        MaterialConditionalUndesignated=0,
        UniversalDesignated=0,
        UniversalNegatedDesignated=0,
        UniversalNegatedUndesignated=0,
        UniversalUndesignated=0)


    def test_known_branchable_values(self):
        for rulecls in self.logic.Rules.all():
            try:
                value = self.exp[rulecls.name]
            except KeyError:
                raise
            self.assertEqual(rulecls.branching, value)