from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

class Base(BaseCase):
    logic = 'K3W'

class TestRules(Base, autorules=True):

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
        sdn = self.sdnode
        tab, b = self.bt(('NKab', False))
        tab.step()
        b1, b2, b3 = tab
        self.assertTrue(b1.has(sdn('a', False)))
        self.assertTrue(b1.has(sdn('Na', False)))
        self.assertTrue(b2.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('Nb', False)))
        self.assertTrue(b3.has(sdn('a', True)))
        self.assertTrue(b3.has(sdn('b', True)))

    def bt(self, *nitems):
        tab = self.tab()
        b = tab.branch()
        b.extend({'sentence': self.p(s), 'designated': d}
            for s,d in nitems)
        return (tab, b)

class TestArguments(Base, autoargs=True):

    def test_arguments_various(self):
        self.invalid_tab('ANAabNa', 'Na')
        self.invalid_tab('AaTb', 'a')
        self.invalid_tab('AUabNUab')

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FNFNNNFNT',
        Disjunction = 'FNTNNNTNT',
        MaterialConditional = 'TNTNNNFNT',
        MaterialBiconditional = 'TNFNNNFNT',
        Conditional = 'TNTNNNFNT',
        Biconditional = 'TNFNNNFNT',
    )


class TestOptimizations(Base):
    def test_optimize1(self):
        tab = self.tab()
        tab.branch().extend([
            {'sentence': self.p('ANaUab'), 'designated': False},
            {'sentence': self.p('NANaUab'), 'designated': False}])
        step = tab.step()
        self.assertEqual(step.rule.name, 'DisjunctionNegatedUndesignated')

class TestModels(Base):

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
