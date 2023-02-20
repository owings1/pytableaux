from .. import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *

class Base(BaseCase):
    logic = 'GO'

class TestGO(Base):

    def test_truth_table_assertion(self):
        tbl = self.m().truth_table('Assertion')
        self.assertEqual(tbl.outputs[0], 'F')
        self.assertEqual(tbl.outputs[1], 'F')
        self.assertEqual(tbl.outputs[2], 'T')

    def test_truth_table_negation(self):
        tbl = self.m().truth_table('Negation')
        self.assertEqual(tbl.outputs[0], 'T')
        self.assertEqual(tbl.outputs[1], 'N')
        self.assertEqual(tbl.outputs[2], 'F')

    def test_truth_table_disjunction(self):
        tbl = self.m().truth_table('Disjunction')
        self.assertEqual(tbl.outputs[0], 'F')
        self.assertEqual(tbl.outputs[1], 'F')
        self.assertEqual(tbl.outputs[2], 'T')

    def test_truth_table_conjunction(self):
        tbl = self.m().truth_table('Conjunction')
        self.assertEqual(tbl.outputs[0], 'F')
        self.assertEqual(tbl.outputs[1], 'F')
        self.assertEqual(tbl.outputs[8], 'T')

    def test_truth_table_mat_cond(self):
        tbl = self.m().truth_table('MaterialConditional')
        self.assertEqual(tbl.outputs[0], 'T')
        self.assertEqual(tbl.outputs[1], 'T')
        self.assertEqual(tbl.outputs[4], 'F')

    def test_truth_table_mat_bicond(self):
        tbl = self.m().truth_table('MaterialBiconditional')
        self.assertEqual(tbl.outputs[0], 'T')
        self.assertEqual(tbl.outputs[1], 'F')
        self.assertEqual(tbl.outputs[4], 'F')

    def test_truth_table_cond(self):
        tbl = self.m().truth_table('Conditional')
        self.assertEqual(tbl.outputs[0], 'T')
        self.assertEqual(tbl.outputs[3], 'F')
        self.assertEqual(tbl.outputs[4], 'T')

    def test_truth_table_bicond(self):
        tbl = self.m().truth_table('Biconditional')
        self.assertEqual(tbl.outputs[0], 'T')
        self.assertEqual(tbl.outputs[4], 'T')
        self.assertEqual(tbl.outputs[7], 'F')

    def test_MaterialConditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': self.p('NCab'), 'designated': True})
        proof.step()
        self.assertTrue(branch.has({'sentence': self.p('Na'), 'designated': False}))
        self.assertTrue(branch.has({'sentence': self.p('b'), 'designated': False}))

    def test_MaterialBionditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': self.p('NEab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        self.assertTrue(b1.has({'sentence': self.p('Na'), 'designated': False}))
        self.assertTrue(b1.has({'sentence': self.p('b'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('a'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('Nb'), 'designated': False}))

    def test_ConditionalDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': self.p('Uab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        self.assertTrue(b1.has({'sentence': self.p('ANab'), 'designated': True}))
        self.assertTrue(b2.has({'sentence': self.p('a'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('b'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('Na'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('Nb'), 'designated': False}))

    def test_ConditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': self.p('NUab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        self.assertTrue(b1.has({'sentence': self.p('a'), 'designated': True}))
        self.assertTrue(b1.has({'sentence': self.p('b'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('Na'), 'designated': False}))
        self.assertTrue(b2.has({'sentence': self.p('Nb'), 'designated': True}))

    def test_BiconditionalDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': self.p('Bab'), 'designated': True})
        proof.step()
        self.assertTrue(branch.has({'sentence': self.p('Uab'), 'designated': True}))
        self.assertTrue(branch.has({'sentence': self.p('Uba'), 'designated': True}))

    def test_BiconditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': self.p('NBab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        self.assertTrue(b1.has({'sentence': self.p('NUab'), 'designated': True}))
        self.assertTrue(b2.has({'sentence': self.p('NUba'), 'designated': True}))

    def test_AssertionUndesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': self.p('Ta'), 'designated': False})
        proof.step()
        self.assertTrue(branch.has({'sentence': self.p('a'), 'designated': False}))

    def test_AssertionNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': self.p('NTa'), 'designated': True})
        proof.step()
        self.assertTrue(branch.has({'sentence': self.p('a'), 'designated': False}))

    def test_AssertionNegatedUndesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': self.p('NTa'), 'designated': False})
        proof.step()
        self.assertTrue(branch.has({'sentence': self.p('a'), 'designated': True}))

    def test_valid_neg_exist_from_univ(self):
        self.tab('Quantifier Interdefinability 1')

    def test_valid_neg_univ_from_exist(self):
        self.valid_tab('Quantifier Interdefinability 3')

    def test_valid_demorgan_3(self):
        self.valid_tab('DeMorgan 3')

    def test_invalid_demorgan_1(self):
        self.invalid_tab('DeMorgan 1')

    def test_invalid_exist_from_neg_univ(self):
        self.invalid_tab('Quantifier Interdefinability 2')

    def test_invalid_univ_from_neg_exist(self):
        self.invalid_tab('Quantifier Interdefinability 4')

    def test_valid_prior_b3e_rule_defect2(self):
        arg = self.parg('AANaTbNa', 'Na')
        proof = Tableau(self.logic, arg)
        proof.build()
        self.assertTrue(proof.valid)

    def test_branching_complexity_inherits_branchables(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': self.p('Kab'), 'designated': False})
        node = branch[0]
        self.assertEqual(self.logic.TableauxSystem.branching_complexity(node), 0)