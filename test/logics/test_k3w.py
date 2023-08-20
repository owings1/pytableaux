from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

class Base(BaseCase):
    logic = 'K3W'

class TestRules(Base, autorules=True): pass
class TestAutoArgs(Base, autoargs=True): pass

class TestClosure(Base):

    def test_GlutClosure(self):
        self.rule_eg('GlutClosure')

class TestOperators(Base):

    def test_Conjunction(self):
        self.valid_tab('LNC')

    def test_Disjunction(self):
        self.invalid_tab('LEM')

    def test_arguments(self):

        self.valid_tab('Conditional Contraction')
        self.invalid_tab('Addition')
        self.invalid_tab('ANAabNa', 'Na')
        self.invalid_tab('AaTb', 'a')
        self.valid_tab('DeMorgan 1')
        self.valid_tab('DeMorgan 2')
        self.valid_tab('DeMorgan 3')
        self.valid_tab('DeMorgan 4')
        self.invalid_tab('AUabNUab')

    def bt(self, *nitems):
        tab = self.tab()
        b = tab.branch()
        b.extend({'sentence': self.p(s), 'designated': d}
            for s,d in nitems)
        return (tab, b)

    def test_rule_MaterialBiconditionalDesignated_step(self):
        s1, s2 = self.pp('Eab', 'KCabCba')
        tab, b = self.bt((s1, True))
        tab.step()
        self.assertTrue(b.has({'sentence': s2, 'designated': True}))

    def test_rule_MaterialBiconditionalNegatedDesignated_step(self):
        s1, s2 = self.pp('NEab', 'NKCabCba')
        tab, b = self.bt((s1, True))
        tab.step()
        rule = tab.history[0].rule
        self.assertEqual(rule.name, 'MaterialBiconditionalNegatedDesignated')
        self.assertTrue(b.has({'sentence': s2, 'designated': True}))

    def test_rule_ConjunctionNegatedUndesignated_step(self):
        tab, b = self.bt(('NKab', False))
        tab.step()
        b1, b2, b3 = tab
        self.assertTrue(b1.has({'sentence': self.p('a'), 'designated': False}))
        self.assertTrue(b1.has({'sentence': self.p('Na'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('b'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('Nb'), 'designated': False}))
        self.assertTrue(b3.has({'sentence': self.p('a'), 'designated': True}))
        self.assertTrue(b3.has({'sentence': self.p('b'), 'designated': True}))

class TestOptimizations(Base):
    def test_optimize1(self):
        tab = self.tab()
        tab.branch().extend([
            {'sentence': self.p('ANaUab'), 'designated': False},
            {'sentence': self.p('NANaUab'), 'designated': False}])
        step = tab.step()
        self.assertEqual(step.rule.name, 'DisjunctionNegatedUndesignated')

class TestModels(Base):

    def test_truth_table_conjunction(self):
        tbl = self.m().truth_table(Operator.Conjunction)
        self.assertEqual(tbl.outputs[0], 'F')
        self.assertEqual(tbl.outputs[3], 'N')
        self.assertEqual(tbl.outputs[8], 'T')

    def test_models_with_opaques_observed_fail(self):
        # this was because sorting of constants had not been implemented.
        # it was only observed when we were sorting predicated sentences
        # that ended up in the opaques of a model.
        arg = self.parg('VxMFx', 'VxUFxSyMFy', 'Fm')
        proof = Tableau(self.logic, arg, is_build_models=True, max_steps=100)
        proof.build()
        self.assertTrue(proof.invalid)
        for branch in proof.open:
            model = branch.model
            model.get_data()
