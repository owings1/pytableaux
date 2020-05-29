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

def example_proof(logic, name, is_build=True, is_models=True):
    arg = examples.argument(name)
    proof = tableau(logic, arg)
    if is_build:
        proof.build(models=is_models)
    return proof

def empty_proof():
    return tableau(None, None)

class LogicTester(object):

    def example_proof(self, name, **kw):
        return example_proof(self.logic, name, **kw)

class TestFDE(LogicTester):

    logic = get_logic('FDE')

    def test_Closure_example(self):
        proof = tableau(self.logic)
        proof.get_rule(self.logic.TableauxRules.Closure).example()
        proof.build()
        assert len(proof.branches) == 1
        assert proof.valid

    def test_ConjunctionNegatedDesignated_example_node(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('ConjunctionNegatedDesignated')
        props = rule.example_node()
        assert props['sentence'].operator == 'Negation'
        assert props['sentence'].operand.operator == 'Conjunction'
        assert props['designated']

    def test_ExistentialUndesignated_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('ExistentialUndesignated')
        rule.example()
        s = examples.quantified('Existential')
        branch = proof.branches[0]
        assert branch.has({'sentence': s, 'designated': False})

    def test_valid_addition(self):
        proof = self.example_proof('Addition')
        assert proof.valid

    def test_valid_univ_from_neg_exist_1(self):
        proof = self.example_proof('Universal from Negated Existential')
        assert proof.valid

    def test_valid_neg_assert_a_implies_a(self):
        arg = argument(premises=['NTa'], conclusion='Na', notation='polish')
        proof = tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_invalid_lem(self):
        proof = self.example_proof('Law of Excluded Middle')
        assert not proof.valid

    def test_invalid_mat_bicond_elim_3(self):
        proof = self.example_proof('Material Biconditional Elimination 3')
        assert not proof.valid

    def test_invalid_univ_from_exist(self):
        proof = self.example_proof('Universal from Existential')
        assert not proof.valid

    def test_invalid_lnc_build_model(self):
        proof = self.example_proof('Law of Non-contradiction')
        model = proof.branches[0].model
        assert not proof.valid
        assert model.value_of(parse('a')) == model.char_values['B']

    def test_model_b_value_atomic_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': negate(s), 'designated': True}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 0.75

    def test_model_univ_t_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('Fm', examples.vocabulary)
        branch.add({'sentence': s, 'designated': True})
        s1 = parse('VxFx', examples.vocabulary)
        model = branch.make_model()
        assert model.value_of(s1) == 1

    def test_model_exist_b_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('Fm', examples.vocabulary)
        s1 = parse('Fn', examples.vocabulary)
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': negate(s), 'designated': True},
            {'sentence': s1, 'designated': False},
            {'sentence': negate(s1), 'designated': False},
        ])
        s2 = parse('SxFx', examples.vocabulary)
        model = branch.make_model()
        assert model.value_of(s2) == 0.75

    def test_model_necessity_opaque_des_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('La')
        branch.add({'sentence': s, 'designated': True})
        model = branch.make_model()
        assert model.value_of(s) in set([0.75, 1])

    def test_model_necessity_opaque_b_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('La')
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': negate(s), 'designated': True}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 0.75

    def test_model_atomic_undes_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': False}
        ])
        model = branch.make_model()
        assert model.value_of(s) in set([0, 0.25])

    def test_model_atomic_t_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': negate(s), 'designated': False}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 1

    def test_model_atomic_f_value_branch(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': False},
            {'sentence': negate(s), 'designated': True}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 0

    def test_model_is_opaque_neg_necessity(self):
        model = self.logic.Model()
        s = parse('NLa')
        assert model.is_sentence_opaque(s)


class TestK3(LogicTester):

    logic = get_logic('K3')

    def test_Closure_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.Closure)
        rule.example()
        proof.build()
        assert len(proof.branches) == 1
        assert proof.valid
        
    def test_valid_bicond_elim_1(self):
        proof = self.example_proof('Biconditional Elimination 1')
        assert proof.valid

    def test_invalid_lem(self):
        proof = self.example_proof('Law of Excluded Middle')
        assert not proof.valid

class TestK3W(LogicTester):

    logic = get_logic('k3w')

    def test_truth_table_conjunction(self):
        tbl = truth_table(self.logic, 'Conjunction')
        assert tbl['outputs'][0] == 0
        assert tbl['outputs'][3] == 0.5
        assert tbl['outputs'][8] == 1

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

    def test_invalid_prior_rule_defect(self):
        arg = argument('ANAabNa', premises=['Na'], notation='polish')
        proof = tableau(self.logic, arg)
        proof.build()
        assert not proof.valid

class TestB3E(LogicTester):

    logic = get_logic('B3E')

    def test_truth_table_assertion(self):
        tbl = truth_table(self.logic, 'Assertion')
        assert tbl['outputs'][0] == 0
        assert tbl['outputs'][1] == 0
        assert tbl['outputs'][2] == 1

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][3] == 1
        assert tbl['outputs'][4] == 1
        assert tbl['outputs'][7] == 0

    def test_truth_table_biconditional(self):
        tbl = truth_table(self.logic, 'Biconditional')
        assert tbl['outputs'][2] == 0
        assert tbl['outputs'][4] == 1
        assert tbl['outputs'][7] == 0
        
    def test_valid_cond_contraction(self):
        proof = self.example_proof('Conditional Contraction')
        assert proof.valid

    def test_valid_bicond_elim_1(self):
        proof = self.example_proof('Biconditional Elimination 1')
        assert proof.valid

    def test_valid_bicond_elim_3(self):
        proof = self.example_proof('Biconditional Elimination 3')
        assert proof.valid

    def test_valid_bicond_intro_1(self):
        proof = self.example_proof('Biconditional Introduction 1')
        assert proof.valid

    def test_invalid_lem(self):
        proof = self.example_proof('Law of Excluded Middle')
        assert not proof.valid

    def test_invalid_prior_rule_defect(self):
        arg = argument('ANAabNa', premises=['Na'], notation='polish')
        proof = tableau(self.logic, arg)
        proof.build()
        assert not proof.valid

class TestLP(LogicTester):

    logic = get_logic('LP')

    def test_Closure_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.Closure)
        rule.example()
        proof.build()
        assert proof.valid

    def test_valid_material_ident(self):
        proof = self.example_proof('Material Identity')
        assert proof.valid

    def test_invalid_lnc(self):
        proof = self.example_proof('Law of Non-contradiction')
        assert not proof.valid

class TestGO(LogicTester):

    logic = get_logic('GO')

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

    def test_valid_neg_exist_from_univ(self):
        proof = self.example_proof('Negated Existential from Universal')
        assert proof.valid

    def test_valid_neg_univ_from_exist(self):
        proof = self.example_proof('Negated Universal from Existential')
        assert proof.valid

    def test_valid_demorgan_3(self):
        proof = self.example_proof('DeMorgan 3')
        assert proof.valid

    def test_invalid_demorgan_1(self):
        proof = self.example_proof('DeMorgan 1')
        assert not proof.valid

    def test_invalid_exist_from_neg_univ(self):
        proof = self.example_proof('Existential from Negated Universal')
        assert not proof.valid

    def test_invalid_univ_from_neg_exist(self):
        proof = self.example_proof('Universal from Negated Existential')
        assert not proof.valid

class TestCPL(LogicTester):

    logic = get_logic('CPL')

    def test_Closure_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('Closure')
        rule.example()
        assert len(proof.branches) == 1

    def test_SelfIdentityClosure_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('SelfIdentityClosure')
        rule.example()
        assert len(proof.branches) == 1

    def test_IdentityIndiscernability_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('IdentityIndiscernability')
        rule.example()
        assert len(proof.branches) == 1

    def test_valid_simplification(self):
        proof = self.example_proof('Simplification')
        assert proof.valid

    def test_invalid_syllogism(self):
        proof = self.example_proof('Syllogism')
        assert not proof.valid

    def test_read_model_deny_antec(self):
        proof = self.example_proof('Denying the Antecedent')
        model = self.logic.Model()
        branch = list(proof.open_branches())[0]
        self.logic.TableauxSystem.read_model(model, branch)
        s = atomic(0, 0)
        assert model.value_of(s) == 0
        assert model.value_of(negate(s)) == 1

    def test_read_model_extract_disj_2(self):
        proof = self.example_proof('Extracting a Disjunct 2')
        model = self.logic.Model()
        branch = list(proof.open_branches())[0]
        self.logic.TableauxSystem.read_model(model, branch)
        s = atomic(0, 0)
        assert model.value_of(s) == 1
        assert model.value_of(negate(s)) == 0

    def test_read_model_no_proof_predicated(self):
        branch = TableauxSystem.Branch()
        s1 = parse('Fm', vocabulary=examples.vocabulary)
        branch.add({'sentence': s1})
        model = self.logic.Model()
        self.logic.TableauxSystem.read_model(model, branch)
        assert model.value_of(s1) == 1
        
    def test_model_add_access_not_impl(self):
        model = self.logic.Model()
        with pytest.raises(NotImplementedError):
            model.add_access(0, 0)

    def test_model_set_literal_value_predicated1(self):
        model = self.logic.Model()
        m = constant(0, 0)
        n = constant(1, 0)
        s = predicated('Identity', [m, n])
        model.set_literal_value(s, 1)
        res = model.value_of(s)
        assert res == 1

    def test_model_opaque_necessity_branch_make_model(self):
        s = parse('La')
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s})
        model = branch.make_model()
        assert model.value_of(s) == 1

    def test_model_opaque_neg_necessity_branch_make_model(self):
        s = parse('La')
        proof = tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': negate(s)})
        model = branch.make_model()
        assert model.value_of(s) == 0

    def test_model_get_data_triv(self):
        s = parse('a')
        model = self.logic.Model()
        model.set_literal_value(s, 1)
        model.finish()
        data = model.get_data()
        assert 'Atomics' in data

class TestCFOL(LogicTester):

    logic = get_logic('CFOL')

    def test_valid_syllogism(self):
        proof = example_proof('cfol', 'Syllogism')
        assert proof.valid

    def test_invalid_possibility_addition(self):
        proof = example_proof('cfol', 'Possibility Addition')
        assert not proof.valid

    def test_model_get_data_triv(self):
        s = parse('a')
        model = self.logic.Model()
        model.set_literal_value(s, 1)
        model.finish()
        data = model.get_data()
        assert 'Atomics' in data

class TestK(LogicTester):

    logic = get_logic('K')

    def test_Closure_example(self):
        rule = self.logic.TableauxRules.Closure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_SelfIdentityClosure_example(self):
        rule = self.logic.TableauxRules.SelfIdentityClosure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_Possibility_example_node(self):
        rule = self.logic.TableauxRules.Possibility(empty_proof())
        props = rule.example_node()
        assert props['world'] == 0

    def test_Existential_example_node(self):
        rule = self.logic.TableauxRules.Existential(empty_proof())
        props = rule.example_node()
        assert props['sentence'].quantifier == 'Existential'

    def test_DisjunctionNegated_example_node(self):
        rule = self.logic.TableauxRules.DisjunctionNegated(empty_proof())
        props = rule.example_node()
        assert props['sentence'].operator == 'Negation'

    def test_Universal_example(self):
        rule = self.logic.TableauxRules.Universal(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_Necessity_example(self):
        rule = self.logic.TableauxRules.Necessity(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_IdentityIndiscernability_example(self):
        rule = self.logic.TableauxRules.IdentityIndiscernability(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_IdentityIndiscernability_not_applies(self):
        proof = empty_proof()
        branch = proof.branch()
        branch.add({'sentence': parse('Imm'), 'world': 0})
        branch.add({'sentence': parse('Fs', vocabulary=examples.vocabulary), 'world': 0})
        rule = self.logic.TableauxRules.IdentityIndiscernability(proof)
        res = rule.applies_to_branch(branch)
        assert not res
        
    def test_valid_conjunction_introduction(self):
        proof = self.example_proof('Conjunction Introduction')
        assert proof.valid

    def test_valid_addition(self):
        proof = self.example_proof('Addition')
        assert proof.valid

    def test_valid_self_identity_1(self):
        proof = self.example_proof('Self Identity 1')
        assert proof.valid
        
    def test_valid_nec_dist(self):
        proof = self.example_proof('Necessity Distribution')
        assert proof.valid

    def test_valid_material_bicond_elim_1(self):
        proof = self.example_proof('Material Biconditional Elimination 1')
        assert proof.valid

    def test_valid_material_bicond_intro_1(self):
        proof = self.example_proof('Material Biconditional Introduction 1')
        assert proof.valid

    def test_valid_disj_syllogism(self):
        proof = self.example_proof('Disjunctive Syllogism')
        assert proof.valid

    def test_valid_disj_syllogism_2(self):
        proof = self.example_proof('Disjunctive Syllogism 2')
        assert proof.valid
        
    def test_valid_assert_elim_1(self):
        proof = self.example_proof('Assertion Elimination 1')
        assert proof.valid

    def test_valid_assert_elim_2(self):
        proof = self.example_proof('Assertion Elimination 2')
        assert proof.valid

    def test_valid_nec_elim(self):
        proof = self.example_proof('Necessity Distribution')
        assert proof.valid

    def test_valid_modal_tranform_2(self):
        proof = self.example_proof('Modal Transformation 2')
        assert proof.valid

    def test_valid_ident_indiscern_1(self):
        proof = self.example_proof('Identity Indiscernability 1')
        assert proof.valid

    def test_valid_ident_indiscern_2(self):
        proof = self.example_proof('Identity Indiscernability 2')
        assert proof.valid
        
    def test_invalid_nec_elim(self):
        proof = self.example_proof('Necessity Elimination')
        assert not proof.valid

    def test_read_model_proof_deny_antec(self):
        proof = self.example_proof('Denying the Antecedent')
        model = self.logic.Model()
        branch = list(proof.open_branches())[0]
        self.logic.TableauxSystem.read_model(model, branch)
        s = atomic(0, 0)
        assert model.value_of(s, world=0) == 0
        assert model.value_of(negate(s), world=0) == 1

    def test_read_model_no_proof_atomic(self):
        model = self.logic.Model()
        branch = TableauxSystem.Branch()
        branch.add({'sentence': atomic(0, 0), 'world': 0})
        self.logic.TableauxSystem.read_model(model, branch)
        assert model.value_of(atomic(0, 0), world=0) == 1

    def test_read_model_no_proof_predicated(self):
        model = self.logic.Model()
        branch = TableauxSystem.Branch()
        s1 = parse('Imn')
        branch.add({'sentence': s1, 'world': 0})
        self.logic.TableauxSystem.read_model(model, branch)
        assert model.value_of(s1, world=0) == 1

    def test_read_model_no_proof_access(self):
        model = self.logic.Model()
        branch = TableauxSystem.Branch()
        branch.add({'world1': 0, 'world2': 1})
        self.logic.TableauxSystem.read_model(model, branch)
        assert model.has_access(0, 1)

    def test_model_value_of_atomic_unassigned(self):
        model = self.logic.Model()
        s = atomic(0, 0)
        res = model.value_of_atomic(s, 0)
        assert res == model.unassigned_value

    def test_model_set_predicated_value1(self):
        model = self.logic.Model()
        m = constant(0, 0)
        n = constant(1, 0)
        s = predicated('Identity', [m, n])
        model.set_predicated_value(s, 1, 0)
        res = model.value_of(s, world=0)
        assert res == 1

    def test_model_add_access_sees(self):
        model = self.logic.Model()
        model.add_access(0, 0)
        assert 0 in model.visibles(0)

    def test_model_possibly_a_with_access_true(self):
        model = self.logic.Model()
        a = atomic(0, 0)
        model.add_access(0, 1)
        model.set_atomic_value(a, 1, 1)
        res = model.value_of(operate('Possibility', [a]), world=0)
        assert res == 1

    def test_model_possibly_a_no_access_false(self):
        model = self.logic.Model()
        a = atomic(0, 0)
        model.set_atomic_value(a, 1, 1)
        res = model.value_of(operate('Possibility', [a]), world=0)
        assert res == 0

    def test_model_nec_a_no_access_true(self):
        model = self.logic.Model()
        a = atomic(0, 0)
        res = model.value_of(operate('Necessity', [a]), world=0)
        assert res == 1

    def test_model_nec_a_with_access_false(self):
        model = self.logic.Model()
        a = atomic(0, 0)
        model.set_atomic_value(a, 1, 0)
        model.set_atomic_value(a, 0, 1)
        model.add_access(0, 1)
        model.add_access(0, 0)
        res = model.value_of(operate('Necessity', [a]), world=0)
        assert res == 0

    def test_model_existence_user_pred_true(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = quantify('Existential', x, s2)

        model = self.logic.Model()
        model.set_predicated_value(s1, 1, 0)
        res = model.value_of(s3, world=0)
        assert res == 1

    def test_model_existense_user_pred_false(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = quantify('Existential', x, s2)

        model = self.logic.Model()
        res = model.value_of(s3, world=0)
        assert res == 0

    def test_model_universal_user_pred_true(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = quantify('Universal', x, s2)

        model = self.logic.Model()
        model.set_predicated_value(s1, 1, 0)
        res = model.value_of(s3, world=0)
        assert res == 1

    def test_model_universal_false(self):
        s1 = parse('VxFx', vocabulary=examples.vocabulary)
        s2 = parse('Fm', vocabulary=examples.vocabulary)
        model = self.logic.Model()
        model.set_predicated_value(s2, 0, 0)
        res = model.value_of(s1, world=0)
        assert res == 0

    def test_model_universal_user_pred_false(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = constant(0, 0)
        n = constant(1, 0)
        x = variable(0, 0)
        s1 = predicated('MyPred', [m], v)
        s2 = predicated('MyPred', [x], v)
        s3 = predicated('MyPred', [n], v)
        s4 = quantify('Universal', x, s2)
    
        model = self.logic.Model()
        model.set_predicated_value(s1, 1, 0)
        model.set_predicated_value(s3, 0, 0)
        res = model.value_of(s4, world=0)
        assert res == 0

    def test_model_identity_extension_non_empty_with_sentence(self):
        s = parse('Imn')
        model = self.logic.Model()
        model.set_predicated_value(s, 1, 0)
        extension = model.get_extension(Vocabulary.get_system_predicate('Identity'), 0)
        assert len(extension) > 0
        assert (constant(0, 0), constant(1, 0)) in extension
        
    def test_model_frame_data_has_identity_with_sentence(self):
        s = parse('Imn')
        model = self.logic.Model()
        model.set_predicated_value(s, 1, 0)
        model.finish()
        data = model.get_data()
        assert len(data['Frames']['values']) == 1
        fdata = data['Frames']['values'][0]['value']
        assert len(fdata['Predicates']['values']) == 2
        pdata = fdata['Predicates']['values'][1]
        assert pdata['values'][0]['input'].name == 'Identity'

    def test_model_get_data_with_access_has_2_frames(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 1, world=0)
        model.add_access(0, 1)
        model.finish()
        data = model.get_data()
        assert len(data['Frames']['values']) == 2

class TestD(LogicTester):

    logic = get_logic('D')

    def test_Serial_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('Serial')
        rule.example()
        assert len(proof.branches) == 1

    def test_Serial_applies_to_branch_empty(self):
        proof = tableau(self.logic)
        branch = proof.branch()
        rule = proof.get_rule('Serial')
        res = rule.applies_to_branch(branch)
        assert not res

    def test_valid_serial_inf_1(self):
        proof = self.example_proof('Serial Inference 1')
        assert proof.valid

    def test_invalid_reflex_inf_1(self):
        proof = self.example_proof('Reflexive Inference 1')
        assert not proof.valid

class TestT(LogicTester):

    logic = get_logic('T')

    def test_Reflexive_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.Reflexive)
        rule.example()
        proof.build()
        branch = proof.branches[0]
        assert branch.has({'world1': 0, 'world2': 0})

    def test_valid_np_collapse_1(self):
        proof = self.example_proof('NP Collapse 1')
        assert proof.valid

    def test_invalid_s4_inf_1(self):
        proof = self.example_proof('S4 Inference 1')
        assert not proof.valid

class TestS4(LogicTester):

    logic = get_logic('S4')

    def test_Transitive_example(self):
        proof = tableau(self.logic)
        rule = proof.get_rule('Transitive')
        rule.example()
        proof.build()
        branch = proof.branches[0]
        assert branch.has({'world1': 0, 'world2': 2})

    def test_valid_s4_inf_1(self):
        proof = self.example_proof('S4 Inference 1')
        assert proof.valid

    def test_valid_np_collapse_1(self):
        proof = self.example_proof('NP Collapse 1')
        assert proof.valid

    def test_invalid_s5_cond_inf_1(self):
        proof = self.example_proof('S5 Conditional Inference 1')
        assert not proof.valid

class TestL3(LogicTester):

    logic = get_logic('L3')

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

class TestRM3(LogicTester):

    logic = get_logic('RM3')

    def test_valid_cond_mp(self):
        proof = self.example_proof('Conditional Modus Ponens')
        assert proof.valid