# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ------------------
#
# pytableaux - logics test cases
import pytest

from logic import *
import examples

def validities(logic):
    return get_logic(logic).example_validities()

def invalidities(logic):
    return get_logic(logic).example_invalidities()

def example_proof(logic, name, is_build=True):
    arg = examples.argument(name)
    proof = tableau(logic, arg)
    if is_build:
        proof.build()
    return proof

def empty_proof():
    return tableau(None, None)

class LogicTester(object):

    def example_proof(self, name):
        return example_proof(self.logic, name)

class TestFDE(object):

    def test_examples(self):
        valids = validities('fde')
        invalids = invalidities('fde')
        assert 'Addition' in valids
        assert 'Law of Excluded Middle' in invalids

    def test_ConjunctionNegatedDesignated_example_node(self):
        rule = get_logic('fde').TableauxRules.ConjunctionNegatedDesignated(empty_proof())
        props = rule.example_node()
        assert props['sentence'].operator == 'Negation'
        assert props['sentence'].operand.operator == 'Conjunction'
        assert props['designated']

    def test_valid_addition(self):
        proof = example_proof('fde', 'Addition')
        assert proof.valid

    def test_invalid_lem(self):
        proof = example_proof('fde', 'Law of Excluded Middle')
        assert not proof.valid

class TestK3(object):

    def test_examples(self):
        valids = validities('k3')
        invalids = invalidities('k3')
        assert 'Biconditional Elimination 1' in valids
        assert 'Law of Excluded Middle' in invalids

    def test_valid_bicond_elim_1(self):
        proof = example_proof('k3', 'Biconditional Elimination 1')
        assert proof.valid

    def test_invalid_lem(self):
        proof = example_proof('k3', 'Law of Excluded Middle')
        assert not proof.valid

class TestK3W(LogicTester):

    logic = get_logic('k3w')

    def test_examples(self):
        valids = validities(self.logic)
        invalids = invalidities(self.logic)
        assert 'Conditional Contraction' in valids
        assert 'Addition' in invalids

    def test_truth_table_conjunction(self):
        tbl = truth_table(self.logic, 'Conjunction')
        assert tbl['outputs'][0] == 0
        assert tbl['outputs'][3] == 0.5
        assert tbl['outputs'][8] == 1

    def test_DisjunctionNegatedUndesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('NAab'), 'designated': False})
        proof.step()
        b1, b2, b3, b4 = proof.branches
        assert b1.has({'sentence': parse('a'), 'designated': True})
        assert b1.has({'sentence': parse('b'), 'designated': True})
        assert b2.has({'sentence': parse('a'), 'designated': True})
        assert b2.has({'sentence': parse('Nb'), 'designated': True})
        assert b3.has({'sentence': parse('Na'), 'designated': True})
        assert b3.has({'sentence': parse('b'), 'designated': True})
        assert b4.has({'sentence': parse('a'), 'designated': False})
        assert b4.has({'sentence': parse('Na'), 'designated': False})
        assert b4.has({'sentence': parse('b'), 'designated': False})
        assert b4.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConjunctionNegatedDesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('NKab'), 'designated': True})
        proof.step()
        b1, b2, b3 = proof.branches
        assert b1.has({'sentence': parse('a'), 'designated': True})
        assert b1.has({'sentence': parse('Nb'), 'designated': True})
        assert b2.has({'sentence': parse('Na'), 'designated': True})
        assert b2.has({'sentence': parse('b'), 'designated': True})
        assert b3.has({'sentence': parse('Na'), 'designated': True})
        assert b3.has({'sentence': parse('Nb'), 'designated': True})

    def test_ConjunctionNegatedUndesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('NKab'), 'designated': False})
        proof.step()
        b1, b2, b3 = proof.branches
        assert b1.has({'sentence': parse('a'), 'designated': False})
        assert b1.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})
        assert b3.has({'sentence': parse('a'), 'designated': True})
        assert b3.has({'sentence': parse('b'), 'designated': True})

    def test_MaterialBiconditionalDesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Eab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('KCabCba'), 'designated': True})

    def test_MaterialBiconditionalNegatedDesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NEab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('NKCabCba'), 'designated': True})

    def test_valid_cond_contraction(self):
        proof = self.example_proof('Conditional Contraction')
        assert proof.valid

    def test_invalid_addition(self):
        proof = self.example_proof('Addition')
        assert not proof.valid

class TestB3E(object):

    def test_examples(self):
        valids = validities('b3e')
        invalids = invalidities('b3e')
        assert 'Conditional Contraction' in valids
        assert 'Triviality 1' in invalids

    def test_valid_cond_contraction(self):
        proof = example_proof('b3e', 'Conditional Contraction')
        assert proof.valid

    def test_invalid_lem(self):
        proof = example_proof('b3e', 'Law of Excluded Middle')
        assert not proof.valid

class TestLP(object):

    def test_examples(self):
        valids = validities('lp')
        invalids = invalidities('lp')
        assert 'Biconditional Identity' in valids
        assert 'Law of Non-contradiction' in invalids

    def test_valid_material_ident(self):
        proof = example_proof('lp', 'Material Identity')
        assert proof.valid

    def test_invalid_lnc(self):
        proof = example_proof('lp', 'Law of Non-contradiction')
        assert not proof.valid

class TestGO(LogicTester):

    logic = get_logic('go')

    def test_examples(self):
        valids = validities('go')
        invalids = invalidities('go')
        assert 'DeMorgan 3' in valids
        assert 'DeMorgan 1' in invalids

    def test_truth_table_assertion(self):
        tbl = truth_table(self.logic, 'Assertion')
        assert tbl['outputs'][0] == 0
        assert tbl['outputs'][1] == 0
        assert tbl['outputs'][2] == 1

    def test_truth_table_negation(self):
        tbl = truth_table(self.logic, 'Negation')
        assert tbl['outputs'][0] == 1
        assert tbl['outputs'][1] == 0.5
        assert tbl['outputs'][2] == 0

    def test_truth_table_disjunction(self):
        tbl = truth_table(self.logic, 'Disjunction')
        assert tbl['outputs'][0] == 0
        assert tbl['outputs'][1] == 0
        assert tbl['outputs'][2] == 1

    def test_truth_table_conjunction(self):
        tbl = truth_table(self.logic, 'Conjunction')
        assert tbl['outputs'][0] == 0
        assert tbl['outputs'][1] == 0
        assert tbl['outputs'][8] == 1

    def test_truth_table_mat_cond(self):
        tbl = truth_table(self.logic, 'Material Conditional')
        assert tbl['outputs'][0] == 1
        assert tbl['outputs'][1] == 1
        assert tbl['outputs'][4] == 0

    def test_truth_table_mat_bicond(self):
        tbl = truth_table(self.logic, 'Material Biconditional')
        assert tbl['outputs'][0] == 1
        assert tbl['outputs'][1] == 0
        assert tbl['outputs'][4] == 0

    def test_truth_table_cond(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][0] == 1
        assert tbl['outputs'][3] == 0
        assert tbl['outputs'][4] == 1

    def test_truth_table_bicond(self):
        tbl = truth_table(self.logic, 'Biconditional')
        assert tbl['outputs'][0] == 1
        assert tbl['outputs'][4] == 1
        assert tbl['outputs'][7] == 0

    def test_MaterialConditionalNegatedDesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NCab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('Na'), 'designated': False})
        assert branch.has({'sentence': parse('b'), 'designated': False})

    def test_MaterialBionditionalNegatedDesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('NEab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('Na'), 'designated': False})
        assert b1.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('a'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConditionalDesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('Uab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('ANab'), 'designated': True})
        assert b2.has({'sentence': parse('a'), 'designated': False})
        assert b2.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConditionalNegatedDesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('NUab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('a'), 'designated': True})
        assert b1.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': True})

    def test_BiconditionalDesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Bab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('Uab'), 'designated': True})
        assert branch.has({'sentence': parse('Uba'), 'designated': True})

    def test_BiconditionalNegatedDesignated_step(self):
        proof = tableau(self.logic)
        proof.branch().add({'sentence': parse('NBab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('NUab'), 'designated': True})
        assert b2.has({'sentence': parse('NUba'), 'designated': True})

    def test_AssertionUndesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Ta'), 'designated': False})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_AssertionNegatedDesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NTa'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_AssertionNegatedUndesignated_step(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NTa'), 'designated': False})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_valid_demorgan_3(self):
        proof = self.example_proof('DeMorgan 3')
        assert proof.valid

    def test_invalid_demorgan_1(self):
        proof = self.example_proof('DeMorgan 1')
        assert not proof.valid

class TestCPL(object):

    def test_examples(self):
        valids = validities('cpl')
        invalids = invalidities('cpl')
        assert 'Simplification' in valids
        assert 'Syllogism' in invalids

    def test_Closure_example(self):
        rule = get_logic('cpl').TableauxRules.Closure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_SelfIdentityClosure_example(self):
        rule = get_logic('cpl').TableauxRules.SelfIdentityClosure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_IdentityIndiscernability_example(self):
        rule = get_logic('cpl').TableauxRules.IdentityIndiscernability(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_valid_simplification(self):
        proof = example_proof('cpl', 'Simplification')
        assert proof.valid

    def test_invalid_syllogism(self):
        proof = example_proof('cpl', 'Syllogism')
        assert not proof.valid

    def test_read_model_deny_antec(self):
        proof = example_proof('cpl', 'Denying the Antecedent')
        lgc = get_logic('cpl')
        model = lgc.Model()
        branch = list(proof.open_branches())[0]
        lgc.TableauxSystem.read_model(model, branch)
        s = atomic(0, 0)
        assert model.value_of(s) == 0
        assert model.value_of(negate(s)) == 1

    def test_read_model_extract_disj_2(self):
        proof = example_proof('cpl', 'Extracting a Disjunct 2')
        lgc = get_logic('cpl')
        model = lgc.Model()
        branch = list(proof.open_branches())[0]
        lgc.TableauxSystem.read_model(model, branch)
        s = atomic(0, 0)
        assert model.value_of(s) == 1
        assert model.value_of(negate(s)) == 0

    def test_read_model_no_proof_predicated(self):
        branch = TableauxSystem.Branch()
        s1 = parse('Fm', vocabulary=examples.vocabulary)
        branch.add({'sentence': s1})
        lgc = get_logic('cpl')
        model = lgc.Model()
        lgc.TableauxSystem.read_model(model, branch)
        assert model.value_of(s1) == 1
        
    def test_model_add_access_not_impl(self):
        lgc = get_logic('cpl')
        model = lgc.Model()
        with pytest.raises(NotImplementedError):
            model.add_access(0, 0)

    def test_model_set_predicated_value1(self):
        lgc = get_logic('cpl')
        model = lgc.Model()
        m = constant(0, 0)
        n = constant(1, 0)
        s = predicated('Identity', [m, n])
        model.set_predicated_value(s, 1)
        res = model.value_of(s)
        assert res == 1


class TestCFOL(object):

    def test_examples(self):
        valids = validities('cfol')
        invalids = invalidities('cfol')
        assert 'Syllogism' in valids
        assert 'Possibility Addition' in invalids

    def test_valid_syllogism(self):
        proof = example_proof('cfol', 'Syllogism')
        assert proof.valid

    def test_invalid_possibility_addition(self):
        proof = example_proof('cfol', 'Possibility Addition')
        assert not proof.valid

class TestK(object):

    def get_logic(self):
        return get_logic('k')

    def new_model(self):
        return self.get_logic().Model()

    def test_examples(self):
        valids = validities('k')
        invalids = invalidities('k')
        assert 'Necessity Distribution' in valids
        assert 'Necessity Elimination' in invalids

    def test_Closure_example(self):
        rule = get_logic('k').TableauxRules.Closure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_SelfIdentityClosure_example(self):
        rule = get_logic('k').TableauxRules.SelfIdentityClosure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_Possibility_example_node(self):
        rule = get_logic('k').TableauxRules.Possibility(empty_proof())
        props = rule.example_node()
        assert props['world'] == 0

    def test_Existential_example_node(self):
        rule = get_logic('k').TableauxRules.Existential(empty_proof())
        props = rule.example_node()
        assert props['sentence'].quantifier == 'Existential'

    def test_DisjunctionNegated_example_node(self):
        rule = get_logic('k').TableauxRules.DisjunctionNegated(empty_proof())
        props = rule.example_node()
        assert props['sentence'].operator == 'Negation'

    def test_Universal_example(self):
        rule = get_logic('k').TableauxRules.Universal(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_Necessity_example(self):
        rule = get_logic('k').TableauxRules.Necessity(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_IdentityIndiscernability_example(self):
        rule = get_logic('k').TableauxRules.IdentityIndiscernability(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_IdentityIndiscernability_not_applies(self):
        proof = empty_proof()
        branch = proof.branch()
        branch.add({'sentence': parse('Imm'), 'world': 0})
        branch.add({'sentence': parse('Fs', vocabulary=examples.vocabulary), 'world': 0})
        rule = self.get_logic().TableauxRules.IdentityIndiscernability(proof)
        res = rule.applies_to_branch(branch)
        assert not res
        
    def test_valid_conjunction_introduction(self):
        proof = example_proof('k', 'Conjunction Introduction')
        assert proof.valid

    def test_valid_addition(self):
        proof = example_proof('k', 'Addition')
        assert proof.valid

    def test_valid_self_identity_1(self):
        proof = example_proof('k', 'Self Identity 1')
        assert proof.valid
        
    def test_valid_nec_dist(self):
        proof = example_proof('k', 'Necessity Distribution')
        assert proof.valid

    def test_valid_material_bicond_elim_1(self):
        proof = example_proof('k', 'Material Biconditional Elimination 1')
        assert proof.valid

    def test_valid_material_bicond_intro_1(self):
        proof = example_proof('k', 'Material Biconditional Introduction 1')
        assert proof.valid

    def test_valid_disj_syllogism(self):
        proof = example_proof('k', 'Disjunctive Syllogism')
        assert proof.valid

    def test_valid_disj_syllogism_2(self):
        proof = example_proof('k', 'Disjunctive Syllogism 2')
        assert proof.valid
        
    def test_valid_assert_elim_1(self):
        proof = example_proof('k', 'Assertion Elimination 1')
        assert proof.valid

    def test_valid_assert_elim_2(self):
        proof = example_proof('k', 'Assertion Elimination 2')
        assert proof.valid

    def test_valid_nec_elim(self):
        proof = example_proof('k', 'Necessity Distribution')
        assert proof.valid

    def test_valid_modal_tranform_2(self):
        proof = example_proof('k', 'Modal Transformation 2')
        assert proof.valid

    def test_valid_ident_indiscern_1(self):
        proof = example_proof('k', 'Identity Indiscernability 1')
        assert proof.valid

    def test_valid_ident_indiscern_2(self):
        proof = example_proof('k', 'Identity Indiscernability 2')
        assert proof.valid
        
    def test_invalid_nec_elim(self):
        proof = example_proof('k', 'Necessity Elimination')
        assert not proof.valid

    def test_read_model_proof_deny_antec(self):
        proof = example_proof('k', 'Denying the Antecedent')
        lgc = get_logic('k')
        model = lgc.Model()
        branch = list(proof.open_branches())[0]
        lgc.TableauxSystem.read_model(model, branch)
        s = atomic(0, 0)
        assert model.value_of(s, 0) == 0
        assert model.value_of(negate(s), 0) == 1

    def test_read_model_no_proof_atomic(self):
        model = self.new_model()
        lgc = self.get_logic()
        branch = TableauxSystem.Branch()
        branch.add({'sentence': atomic(0, 0), 'world': 0})
        lgc.TableauxSystem.read_model(model, branch)
        assert model.value_of(atomic(0, 0), 0) == 1

    def test_read_model_no_proof_predicated(self):
        model = self.new_model()
        lgc = self.get_logic()
        branch = TableauxSystem.Branch()
        s1 = parse('Imn')
        branch.add({'sentence': s1, 'world': 0})
        lgc.TableauxSystem.read_model(model, branch)
        assert model.value_of(s1, 0) == 1

    def test_read_model_no_proof_access(self):
        model = self.new_model()
        lgc = self.get_logic()
        branch = TableauxSystem.Branch()
        branch.add({'world1': 0, 'world2': 1})
        lgc.TableauxSystem.read_model(model, branch)
        assert model.has_access(0, 1)

    def test_model_access_equals(self):
        lgc = get_logic('k')
        a1 = lgc.Model.Access(0, 0)
        a2 = lgc.Model.Access(0, 0)
        assert a1 == a2

    def test_model_access_not_equals(self):
        lgc = get_logic('k')
        a1 = lgc.Model.Access(0, 0)
        a2 = lgc.Model.Access(0, 1)
        assert a1 != a2

    def test_model_get_extension_by_name(self):
        lgc = get_logic('k')
        model = lgc.Model()
        s = parse('Imn', vocabulary=examples.vocabulary)
        model.set_predicated_value(s, 1, 0)
        res = model.get_extension('Identity', 0)
        assert (constant(0, 0), constant(1, 0)) in res

    def test_model_get_atomic_value_unassigned(self):
        model = self.new_model()
        s = atomic(0, 0)
        res = model.get_atomic_value(s, 0)
        assert res == self.get_logic().unassigned_value

    def test_model_value_of_unassigned(self):
        model = self.new_model()
        s = atomic(0, 0)
        model.add_unassignable_sentence(s, 0)
        res = model.value_of(s, 0)
        assert res == self.get_logic().unassigned_value

    def test_model_set_predicated_value1(self):
        lgc = get_logic('k')
        model = lgc.Model()
        m = constant(0, 0)
        n = constant(1, 0)
        s = predicated('Identity', [m, n])
        model.set_predicated_value(s, 1, 0)
        res = model.value_of(s, 0)
        assert res == 1

    def test_model_add_access(self):
        lgc = get_logic('k')
        model = lgc.Model()
        model.add_access(0, 0)
        assert 0 in model.sees[0]

    def test_model_possibly_a_with_access_true(self):
        lgc = get_logic('k')
        model = lgc.Model()
        a = atomic(0, 0)
        model.add_access(0, 1)
        model.set_atomic_value(a, 1, 1)
        res = model.value_of(operate('Possibility', [a]), 0)
        assert res == 1

    def test_model_possibly_a_no_access_false(self):
        lgc = get_logic('k')
        model = lgc.Model()
        a = atomic(0, 0)
        model.set_atomic_value(a, 1, 1)
        res = model.value_of(operate('Possibility', [a]), 0)
        assert res == 0

    def test_model_nec_a_no_access_true(self):
        lgc = get_logic('k')
        model = lgc.Model()
        a = atomic(0, 0)
        res = model.value_of(operate('Necessity', [a]), 0)
        assert res == 1

    def test_model_nec_a_with_access_false(self):
        lgc = get_logic('k')
        model = lgc.Model()
        a = atomic(0, 0)
        model.set_atomic_value(a, 1, 0)
        model.set_atomic_value(a, 0, 1)
        model.add_access(0, 1)
        model.add_access(0, 0)
        res = model.value_of(operate('Necessity', [a]), 0)
        assert res == 0

    def test_model_existence_user_pred_true(self):
        lgc = get_logic('k')
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = quantify('Existential', x, s2)

        model = lgc.Model()
        model.set_predicated_value(s1, 1, 0)
        res = model.value_of(s3, 0)
        assert res == 1

    def test_model_existense_user_pred_false(self):
        lgc = get_logic('k')
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = quantify('Existential', x, s2)

        model = lgc.Model()
        res = model.value_of(s3, 0)
        assert res == 0

    def test_model_universal_user_pred_true(self):
        lgc = get_logic('k')
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = quantify('Universal', x, s2)

        model = lgc.Model()
        model.set_predicated_value(s1, 1, 0)
        res = model.value_of(s3, 0)
        assert res == 1

    def test_model_universal_false(self):
        s1 = parse('VxFx', vocabulary=examples.vocabulary)
        s2 = parse('Fm', vocabulary=examples.vocabulary)
        model = self.new_model()
        model.set_predicated_value(s2, 0, 0)
        res = model.value_of(s1, 0)
        assert res == 0
    # TODO: failing
    #def test_model_universal_user_pred_false(self):
    #    lgc = get_logic('k')
    #    v = Vocabulary()
    #    v.declare_predicate('MyPred', 0, 0, 1)
    #    m = constant(0, 0)
    #    n = constant(1, 0)
    #    x = variable(0, 0)
    #    s1 = predicated('MyPred', [m], v)
    #    s2 = predicated('MyPred', [x], v)
    #    s3 = predicated('MyPred', [n], v)
    #    s4 = quantify('Universal', x, s2)
    #
    #    model = lgc.Model()
    #    model.set_predicated_value(s1, 1, 0)
    #    model.set_predicated_value(s3, 0, 0)
    #    res = model.value_of(s4, 0)
    #    assert res == 1

class TestD(object):

    def test_examples(self):
        valids = validities('d')
        invalids = invalidities('d')
        assert 'Serial Inference 1' in valids
        assert 'Reflexive Inference 1' in invalids

    def test_valid_serial_inf_1(self):
        proof = example_proof('d', 'Serial Inference 1')
        assert proof.valid

    def test_invalid_reflex_inf_1(self):
        proof = example_proof('d', 'Reflexive Inference 1')
        assert not proof.valid

class TestT(object):

    def test_examples(self):
        valids = validities('t')
        invalids = invalidities('t')
        assert 'NP Collapse 1' in valids
        assert 'S4 Inference 1' in invalids

    def test_valid_np_collapse_1(self):
        proof = example_proof('t', 'NP Collapse 1')
        assert proof.valid

    def test_invalid_s4_inf_1(self):
        proof = example_proof('t', 'S4 Inference 1')
        assert not proof.valid

class TestS4(object):

    def test_examples(self):
        valids = validities('s4')
        invalids = invalidities('s4')
        assert 'S4 Inference 1' in valids
        assert 'S5 Conditional Inference 1' in invalids

    def test_valid_s4_inf_1(self):
        proof = example_proof('s4', 'S4 Inference 1')
        assert proof.valid

    def test_valid_np_collapse_1(self):
        proof = example_proof('s4', 'NP Collapse 1')
        assert proof.valid

    def test_invalid_s5_cond_inf_1(self):
        proof = example_proof('s4', 'S5 Conditional Inference 1')
        assert not proof.valid

class TestL3(LogicTester):

    logic = get_logic('L3')

    def test_examples(self):
        valids = validities(self.logic)
        invalids = invalidities(self.logic)
        assert 'Conditional Identity' in valids
        assert 'Material Identity' in invalids

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][3] == 0.5
        assert tbl['outputs'][4] == 1
        assert tbl['outputs'][6] == 0
        
    def test_valid_cond_identity(self):
        proof = self.example_proof('Conditional Identity')
        assert proof.valid

    def test_valid_cond_mp(self):
        proof = self.example_proof('Conditional Modus Ponens')
        assert proof.valid

    def test_valid_bicond_elim_1(self):
        proof = self.example_proof('Biconditional Elimination 1')
        assert proof.valid

    def test_valid_bicond_elim_3(self):
        proof = self.example_proof('Biconditional Elimination 3')
        assert proof.valid

    def test_valid_bicond_intro_3(self):
        proof = self.example_proof('Biconditional Introduction 3')
        assert proof.valid

    def test_valid_bicond_ident(self):
        proof = self.example_proof('Biconditional Identity')
        assert proof.valid

    def test_invalid_material_identify(self):
        proof = self.example_proof('Material Identity')
        assert not proof.valid