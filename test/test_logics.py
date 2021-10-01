# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
from errors import *
from utils import get_logic
from lexicals import Vocabulary, Atomic, Constant, Predicated, Quantified, \
    Operated, Variable, get_system_predicate
from tableaux import Tableau, Rule, Branch, FilterNodeRule, Node, MaxConstantsTracker
from parsers import parse, parse_argument
from models import truth_table
import examples

def parsex(s):
    return examples.parser.parse(s)

def validities(logic):
    return get_logic(logic).example_validities()

def invalidities(logic):
    return get_logic(logic).example_invalidities()

def example_proof(logic, name, is_build=True, is_models=True):
    arg = examples.argument(name)
    proof = Tableau(logic, arg)
    if is_build:
        proof.build(is_build_models=is_models)
    return proof

def empty_proof():
    return Tableau(None, None)

class LogicTester(object):

    vocab = Vocabulary([
        ('PredF', 0, 0, 1),
        ('PredG', 1, 0, 1),
    ])

    default_notation = 'polish'

    def example_proof(self, name, **kw):
        return example_proof(self.logic, name, **kw)

    def p(self, s, **kw):
        if 'vocab' not in kw:
            kw['vocab'] = self.vocab
        if 'notn' not in kw:
            kw['notn'] = self.default_notation
        return parse(s, **kw)

    def parg(self, conc, *prems, **kw):
        if 'vocab' not in kw:
            kw['vocab'] = self.vocab
        if 'notn' not in kw:
            kw['notn'] = self.default_notation
        return parse_argument(conclusion=conc, premises=prems, **kw)

    def get_rule(self, rule):
        return Tableau(self.logic).get_rule(rule)

    def assert_axiom(self, ax, **kw):
        arg = self.parg(ax, **kw)
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid
        return proof

    def assert_valid(self, conc, *prems, **kw):
        arg = self.parg(conc, *prems, **kw)
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid
        return proof

    def assert_invalid(self, conc, *prems, **kw):
        arg = self.parg(conc, *prems, **kw)
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.invalid
        return proof

    def assert_valid_eg(self, name):
        proof = self.example_proof(name)
        assert proof.valid
        return proof

    def assert_invalid_eg(self, name):
        proof = self.example_proof(name)
        assert proof.invalid
        return proof

class TestFDE(LogicTester):

    logic = get_logic('FDE')

    def test_DesignationClosure_example(self):
        proof = Tableau(self.logic)
        proof.get_rule(self.logic.TableauxRules.DesignationClosure).example()
        proof.build()
        assert len(proof.branches) == 1
        assert proof.valid

    def test_ConjunctionNegatedDesignated_example_node(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('ConjunctionNegatedDesignated')
        props = rule.example_node(proof.branch())
        assert props['sentence'].operator == 'Negation'
        assert props['sentence'].operand.operator == 'Conjunction'
        assert props['designated']

    def test_ExistentialUndesignated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('ExistentialUndesignated')
        rule.example()
        s = examples.quantified('Existential')
        branch = proof.branches[0]
        assert branch.has({'sentence': s, 'designated': False})

    def test_valid_addition(self):
        proof = self.example_proof('Addition')
        assert proof.valid

    def test_valid_univ_from_neg_exist_1(self):
        self.assert_valid_eg('Quantifier Interdefinability 4')

    def test_valid_neg_assert_a_implies_a(self):
        self.assert_valid('Na', 'NTa')

    def test_valid_demorgan_1(self):
        self.assert_valid_eg('DeMorgan 1')

    def test_valid_demorgan_2(self):
        self.assert_valid_eg('DeMorgan 2')

    def test_valid_demorgan_3(self):
        self.assert_valid_eg('DeMorgan 3')

    def test_valid_demorgan_4(self):
        self.assert_valid_eg('DeMorgan 4')

    def test_invalid_lem(self):
        self.assert_invalid_eg('Law of Excluded Middle')

    def test_invalid_mat_bicond_elim_3(self):
        self.assert_invalid_eg('Material Biconditional Elimination 3')

    def test_invalid_lem_model_is_countermodel_to(self):
        proof = self.example_proof('Law of Excluded Middle')
        branch, = list(proof.open_branchset)
        assert branch.model.is_countermodel_to(proof.argument)

    def test_a_thus_b_is_countermodel_to_false(self):
        arg = parse_argument('b', premises=['a'])
        model = self.logic.Model()
        model.set_literal_value(arg.premises[0], 'F')
        model.set_literal_value(arg.conclusion, 'F')
        assert not model.is_countermodel_to(arg)

    def test_invalid_univ_from_exist(self):
        self.assert_invalid_eg('Universal from Existential')

    def test_invalid_lnc_build_model(self):
        proof = self.example_proof('Law of Non-contradiction')
        model = proof.branches[0].model
        assert not proof.valid
        assert model.value_of(parse('a')) == 'B'

    def test_model_b_value_atomic_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': s.negate(), 'designated': True}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 'B'

    def test_model_univ_t_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('Fm', examples.vocabulary)
        branch.add({'sentence': s, 'designated': True})
        s1 = parse('VxFx', examples.vocabulary)
        model = branch.make_model()
        assert model.value_of(s1) == 'T'

    def test_model_exist_b_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('Fm', examples.vocabulary)
        s1 = parse('Fn', examples.vocabulary)
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': s.negate(), 'designated': True},
            {'sentence': s1, 'designated': False},
            {'sentence': s1.negate(), 'designated': False},
        ])
        s2 = parse('SxFx', examples.vocabulary)
        model = branch.make_model()
        assert model.value_of(s2) == 'B'

    def test_model_necessity_opaque_des_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('La')
        branch.add({'sentence': s, 'designated': True})
        model = branch.make_model()
        assert model.value_of(s) in set(['B', 'T'])

    def test_model_necessity_opaque_b_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('La')
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': s.negate(), 'designated': True}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 'B'

    def test_model_atomic_undes_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': False}
        ])
        model = branch.make_model()
        assert model.value_of(s) in set(['F', 'N'])

    def test_model_atomic_t_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': True},
            {'sentence': s.negate(), 'designated': False}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 'T'

    def test_model_atomic_f_value_branch(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        s = parse('a')
        branch.update([
            {'sentence': s, 'designated': False},
            {'sentence': s.negate(), 'designated': True}
        ])
        model = branch.make_model()
        assert model.value_of(s) == 'F'

    def test_model_get_data_various(self):
        s1 = parse('a')
        s2 = parse('Imn')
        model = self.logic.Model()
        model.set_literal_value(s1, 'B')
        model.set_literal_value(s2, 'F')
        res = model.get_data()
        assert 'Atomics' in res

    def test_model_not_impl_various(self):
        s1 = parse('Aab')
        model = self.logic.Model()
        with pytest.raises(NotImplementedError):
            model.set_literal_value(s1, 'T')
        with pytest.raises(NotImplementedError):
            model.value_of_quantified(s1)
        with pytest.raises(NotImplementedError):
            model.truth_function('Foomunction', 'F')

    def test_model_value_of_atomic_unassigned(self):
        s = parse('a')
        model = self.logic.Model()
        res = model.value_of(s)
        assert res == model.unassigned_value

    def test_model_value_of_opaque_unassigned(self):
        s = parse('La')
        model = self.logic.Model()
        res = model.value_of(s)
        assert res == model.unassigned_value

    def test_model_value_error_various(self):
        s1 = parse('La')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'T')
        with pytest.raises(ModelValueError):
            model.set_opaque_value(s1, 'B')
        s2 = parse('a')
        model = self.logic.Model()
        model.set_atomic_value(s2, 'T')
        with pytest.raises(ModelValueError):
            model.set_atomic_value(s2, 'B')
        s3 = parse('Imn')
        model = self.logic.Model()
        model.set_predicated_value(s3, 'T')
        with pytest.raises(ModelValueError):
            model.set_predicated_value(s3, 'N')
        model = self.logic.Model()
        model.set_predicated_value(s3, 'B')
        with pytest.raises(ModelValueError):
            model.set_predicated_value(s3, 'T')
        model = self.logic.Model()
        model.set_predicated_value(s3, 'B')
        with pytest.raises(ModelValueError):
            model.set_predicated_value(s3, 'F')
        model = self.logic.Model()
        model.set_predicated_value(s3, 'F')
        with pytest.raises(ModelValueError):
            model.set_predicated_value(s3, 'N')

    def test_model_read_branch_with_negated_opaque_then_faithful(self):
        arg = parse_argument('a', premises=['NLa', 'b'])
        proof = Tableau(self.logic, arg)
        proof.build(is_build_models=True)
        model = proof.branches[0].model
        assert model.value_of(parse('a')) == 'F'
        assert model.value_of(parse('La')) == 'F'
        assert model.value_of(parse('NLa')) == 'T'
        assert model.is_countermodel_to(arg)

    def test_branching_complexity_undes_0_1(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('a'), 'designated': False})
        node = branch.get_nodes()[0]
        assert proof.branching_complexity(node) == 0

    def test_branching_complexity_undes_1_1(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Kab'), 'designated': False})
        node = branch.get_nodes()[0]
        assert proof.branching_complexity(node) == 1

    def test_branching_complexity_undes_1_2(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NAaNKbc'), 'designated': False})
        node = branch.get_nodes()[0]
        assert node.props['sentence'].operators() == ['Negation', 'Disjunction', 'Negation', 'Conjunction']
        assert proof.branching_complexity(node) == 1

    def test_branching_complexity_undes_1_3(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NAab'), 'designated': False})
        node = branch.get_nodes()[0]
        assert node.props['sentence'].operators() == ['Negation', 'Disjunction']
        assert proof.branching_complexity(node) == 1

    def test_branching_complexity_undes_2_1(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('KaKab'), 'designated': False})
        node = branch.get_nodes()[0]
        assert node.props['sentence'].operators() == ['Conjunction', 'Conjunction']
        assert proof.branching_complexity(node) == 2

    def test_invalid_existential_inside_univ_max_steps(self):
        arg = parse_argument('b', ['VxUFxSyFy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(max_steps=100)
        assert proof.invalid

    def test_observed_model_error_with_quantifiers_and_modals(self):
        arg = parse_argument('b', ['VxUFxSyMFy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(is_build_models=True, max_steps=100)
        assert proof.invalid

    def test_observed_value_of_universal_with_diamond_min_arg_is_an_empty_sequence(self):
        arg = parse_argument('b', ['VxUFxSyMFy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(is_build_models=False, max_steps=100)
        assert proof.invalid
        branch = proof.branches[-1]
        model = self.logic.Model()
        model.read_branch(branch)
        s1 = arg.premises[0]
        assert model.value_of(s1) in model.designated_values

    def test_observed_as_above_reconstruct1(self):
        # solution was to add all constants in set_opaque_value
        s1 = parse('MFs', vocab=self.vocab) # designated
        s2 = parse('MFo', vocab=self.vocab) # designated
        s3 = parse('MFn', vocab=self.vocab) # designated
        s4 = parse('b') # undesignated
        s5 = parse('SyMFy', vocab=self.vocab) # designated
        s6 = parse('VxUFxSyMFy', vocab=self.vocab) # designated
        model = self.logic.Model()
        model.set_opaque_value(s1, 'T')
        model.set_opaque_value(s2, 'T')
        model.set_opaque_value(s3, 'T')
        model.set_literal_value(s4, 'F')
        assert model.value_of(s3) == 'T'
        assert s3 in model.opaques
        assert model.value_of(s5) in model.designated_values

class TestK3(LogicTester):

    logic = get_logic('K3')

    def test_GlutClosure_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.GlutClosure)
        rule.example()
        proof.build()
        assert len(proof.branches) == 1
        assert proof.valid
        
    def test_valid_bicond_elim_1(self):
        self.assert_valid_eg('Biconditional Elimination 1')

    def test_invalid_lem(self):
        self.assert_invalid_eg('Law of Excluded Middle')

    def test_valid_demorgan_1(self):
        self.assert_valid_eg('DeMorgan 1')

    def test_valid_demorgan_2(self):
        self.assert_valid_eg('DeMorgan 2')

    def test_valid_demorgan_3(self):
        self.assert_valid_eg('DeMorgan 3')

    def test_valid_demorgan_4(self):
        self.assert_valid_eg('DeMorgan 4')

class TestK3W(LogicTester):

    logic = get_logic('k3w')

    def test_truth_table_conjunction(self):
        tbl = truth_table(self.logic, 'Conjunction')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][3] == 'N'
        assert tbl['outputs'][8] == 'T'

    def test_ConjunctionNegatedUndesignated_step(self):
        proof = Tableau(self.logic)
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
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Eab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('KCabCba'), 'designated': True})

    def test_MaterialBiconditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NEab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('NKCabCba'), 'designated': True})

    def test_conditional_designated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.ConditionalDesignated)
        rule.example()
        proof.build()
        assert len(proof.history) > 0
        assert proof.history[0]['rule'] == rule

    def test_conditional_undesignated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.ConditionalUndesignated)
        rule.example()
        proof.build()
        assert len(proof.history) > 0
        assert proof.history[0]['rule'] == rule

    def test_valid_cond_contraction(self):
        self.assert_valid_eg('Conditional Contraction')

    def test_invalid_addition(self):
        self.assert_invalid_eg('Addition')

    def test_invalid_prior_rule_defect(self):
        self.assert_invalid('ANAabNa', 'Na')

    def test_invalid_asserted_addition(self):
        self.assert_invalid('AaTb', 'a')

    def test_valid_demorgan_1(self):
        self.assert_valid_eg('DeMorgan 1')

    def test_valid_demorgan_2(self):
        self.assert_valid_eg('DeMorgan 2')

    def test_valid_demorgan_3(self):
        self.assert_valid_eg('DeMorgan 3')

    def test_valid_demorgan_4(self):
        self.assert_valid_eg('DeMorgan 4')

    def test_invalid_cond_lem(self):
        self.assert_invalid('AUabNUab')

    def test_optimize1(self):
        proof = Tableau(self.logic)
        proof.branch().update([
            {'sentence': parse('ANaUab'), 'designated': False},
            {'sentence': parse('NANaUab'), 'designated': False},
        ])
        step = proof.step()
        assert step['rule'].name == 'DisjunctionNegatedUndesignated'

    def test_models_with_opaques_observed_fail(self):
        # this was because sorting of constants had not been implemented.
        # it was only observed when we were sorting predicated sentences
        # that ended up in the opaques of a model.
        arg = parse_argument('VxMFx', ['VxUFxSyMFy', 'Fm'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(is_build_models=True, max_steps=100)
        assert proof.invalid
        for branch in proof.open_branches():
            model = branch.model
            model.get_data()

class TestK3WQ(LogicTester):

    logic = get_logic('K3WQ')

    def test_valid_quantifier_interdefinability_1(self):
        self.assert_valid_eg('Quantifier Interdefinability 1')

    def test_valid_quantifier_interdefinability_2(self):
        self.assert_valid_eg('Quantifier Interdefinability 2')
        
    def test_valid_quantifier_interdefinability_3(self):
        self.assert_valid_eg('Quantifier Interdefinability 3')

    def test_valid_quantifier_interdefinability_4(self):
        self.assert_valid_eg('Quantifier Interdefinability 4')

    def test_valid_existential_to_if_a_then_a(self):
        self.assert_valid('CFmFm', 'SxFx')
        # arg = parse_argument('CFmFm', ['SxFx'], vocab=self.vocab)
        # proof = Tableau(self.logic, arg).build()
        # assert proof.valid

    def test_invalid_existential_from_predicate_sentence_countermodel(self):
        arg = parse_argument('SxFx', ['Fm'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(is_build_models=True)
        assert proof.invalid
        proof2 = self.assert_invalid('SxFx', 'Fm')
        
        # arg = proof.argument
        branch = list(proof.open_branches())[0]
        model = branch.model
        assert model.value_of(self.p('Fn')) == 'N'
        assert model.value_of(self.p('Fm')) == 'T'
        assert model.value_of(self.p('SxFx')) in {'F', 'N'}
        assert model.is_countermodel_to(arg)

    def test_invalid_universal_from_predicate_sentence_countermodel(self):
        arg = parse_argument('VxFx', ['Fm'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(is_build_models=True)
        assert proof.invalid
        branch = list(proof.open_branches())[0]
        model = branch.model
        assert model.value_of(self.p('Fm')) == 'T'
        assert model.value_of(self.p('VxFx')) in {'F', 'N'}
        assert model.is_countermodel_to(arg)

class TestB3E(LogicTester):

    logic = get_logic('B3E')

    def test_truth_table_assertion(self):
        tbl = truth_table(self.logic, 'Assertion')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][2] == 'T'

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][3] == 'T'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][7] == 'F'

    def test_truth_table_biconditional(self):
        tbl = truth_table(self.logic, 'Biconditional')
        assert tbl['outputs'][2] == 'F'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][7] == 'F'
        
    def test_valid_cond_contraction(self):
        self.assert_valid_eg('Conditional Contraction')

    def test_valid_bicond_elim_1(self):
        self.assert_valid_eg('Biconditional Elimination 1')

    def test_valid_bicond_elim_3(self):
        self.assert_valid_eg('Biconditional Elimination 3')

    def test_valid_bicond_intro_1(self):
        self.assert_valid_eg('Biconditional Introduction 1')

    def test_invalid_lem(self):
        self.assert_invalid_eg('Law of Excluded Middle')

    def test_invalid_prior_rule_defect(self):
        arg = parse_argument('ANAabNa', premises=['Na'], notn='polish')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert not proof.valid

    def test_valid_prior_rule_defect2(self):
        arg = parse_argument('AANaTbNa', premises=['Na'], notn='polish')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_valid_asserted_addition(self):
        arg = parse_argument('AaTb', premises=['a'], notn='polish')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_valid_cond_lem(self):
        proof = Tableau(self.logic, parse_argument('AUabNUab')).build()
        assert proof.valid

class TestL3(LogicTester):

    logic = get_logic('L3')

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][3] == 'N'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][6] == 'F'
        
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

    def test_invalid_cond_contraction(self):
        proof = self.example_proof('Conditional Contraction')
        assert not proof.valid

    def test_invalid_cond_pseudo_contraction(self):
        proof = self.example_proof('Conditional Pseudo Contraction')
        assert not proof.valid

    def test_valid_bicond_from_mat_bicond(self):
        arg = parse_argument('Bab', premises=['Eab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_invalid_mat_bicon_from_bicond(self):
        arg = parse_argument('Eab', premises=['Bab'])
        proof = Tableau(self.logic, arg).build()
        assert not proof.valid

    def test_invalid_cond_lem(self):
        proof = Tableau(self.logic, parse_argument('AUabNUab')).build()
        assert not proof.valid

class TestG3(LogicTester):

    logic = get_logic('G3')

    def test_invalid_demorgan_8_model(self):
        proof = self.example_proof('DeMorgan 8')
        assert proof.invalid
        model = list(proof.open_branches())[0].model
        assert model.is_countermodel_to(proof.argument)

    def test_valid_demorgan_6(self):
        proof = self.example_proof('DeMorgan 6')
        assert proof.valid

    def test_invalid_lem(self):
        proof = self.example_proof('Law of Excluded Middle')
        assert proof.invalid

    def test_invalid_not_not_a_arrow_a(self):
        # Rescher p.45
        arg = parse_argument('UNNaa')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.invalid

    def test_invalid_not_a_arrow_not_b_arrow_b_arrow_a(self):
        # Rescher p.45
        arg = parse_argument('UUNaNbUba')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.invalid

    def test_valid_a_arrow_b_or_b_arrow_a(self):
        # Rescher p.45
        arg = parse_argument('AUabUba')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_valid_not_not_a_arrow_a_arrow_a_or_not_a(self):
        # Rescher p.45
        arg = parse_argument('UUNNaaAaNa')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_valid_a_dblarrow_a(self):
        arg = parse_argument('Baa')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_valid_a_dblarrow_b_thus_a_arrow_b_and_b_arrow_a(self):
        arg = parse_argument('KUabUba', ['Bab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_valid_a_arrow_b_and_b_arrow_a_thus_a_dblarrow_b(self):
        arg = parse_argument('Bab', ['KUabUba'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_valid_not_a_arrow_b_or_not_b_arrow_a_thus_not_a_dblarrow_b(self):
        arg = parse_argument('NBab', ['ANUabNUba'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_valid_not_a_dblarrow_b_thus_not_a_arrow_b_or_not_b_arrow_a(self):
        arg = parse_argument('ANUabNUba', ['NBab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

class TestLP(LogicTester):

    logic = get_logic('LP')

    def test_GapClosure_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.GapClosure)
        rule.example()
        proof.build()
        assert proof.valid

    def test_valid_material_ident(self):
        proof = self.example_proof('Material Identity')
        assert proof.valid

    def test_case_model_not_a_countermodel(self):
        arg = parse_argument('NBab', premises=['c', 'BcNUab'])
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'F')
        model.set_literal_value(parse('b'), 'T')
        model.set_literal_value(parse('c'), 'B')
        assert model.value_of(arg.premises[1]) == 'B'

    def test_case_bad_rule_neg_bicond_undes(self):
        arg = parse_argument('NBab', premises=['NBab'])
        proof = Tableau(self.logic, arg)
        rule = proof.get_rule(self.logic.TableauxRules.BiconditionalNegatedUndesignated)
        assert rule.get_target(proof.branches[0])

    def test_invalid_lnc(self):
        proof = self.example_proof('Law of Non-contradiction')
        assert not proof.valid

    def test_valid_b_then_a_arrow_b(self):
        arg = parse_argument('Uab', premises=['b'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_invalid_cond_modus_ponens(self):
        proof = self.example_proof('Conditional Modus Ponens')
        assert not proof.valid

    def test_valid_a_not_a_not_b_thus_not_a_arrow_b(self):
        proof = Tableau(self.logic, parse_argument('NUab', ['a', 'Na', 'Nb'])).build()
        assert proof.valid

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_a_arrow_b(self):
        proof = Tableau(self.logic, parse_argument('NUab', ['a', 'UaNUbc'])).build()
        assert not proof.valid

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_b_arrow_c(self):
        # this is an instance of modus ponens
        proof = Tableau(self.logic, parse_argument('NUbc', ['a', 'UaNUbc'])).build()
        assert not proof.valid

    def test_invalid_mp_with_neg_bicon(self):
        arg = parse_argument('NBab', premises=['c', 'BcNUab'])
        proof = Tableau(self.logic, arg).build()
        assert not proof.valid

class TestRM3(LogicTester):

    logic = get_logic('RM3')

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'T'
        assert tbl['outputs'][2] == 'T'
        assert tbl['outputs'][3] == 'F'
        assert tbl['outputs'][4] == 'B'
        assert tbl['outputs'][5] == 'T'
        assert tbl['outputs'][6] == 'F'
        assert tbl['outputs'][7] == 'F'
        assert tbl['outputs'][8] == 'T'

    def test_model_value_of_biconditional(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'B')
        model.set_literal_value(parse('b'), 'F')
        assert model.value_of(parse('Bab')) == 'F'

    def test_valid_cond_mp(self):
        proof = self.example_proof('Conditional Modus Ponens')
        assert proof.valid

    def test_valid_demorgan_1(self):
        proof = self.example_proof('DeMorgan 1')
        assert proof.valid

    def test_valid_demorgan_2(self):
        proof = self.example_proof('DeMorgan 2')
        assert proof.valid

    def test_valid_demorgan_3(self):
        proof = self.example_proof('DeMorgan 3')
        assert proof.valid

    def test_valid_demorgan_4(self):
        proof = self.example_proof('DeMorgan 4')
        assert proof.valid

    def test_invalid_b_then_a_arrow_b(self):
        arg = parse_argument('Uab', premises=['b'])
        proof = Tableau(self.logic, arg).build()
        assert not proof.valid

    def test_valid_cond_modus_ponens(self):
        proof = self.example_proof('Conditional Modus Ponens')
        assert proof.valid

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_a_arrow_b(self):
        proof = Tableau(self.logic, parse_argument('NUab', ['a', 'UaNUbc'])).build()
        assert not proof.valid

    def test_valid_a_a_arrow_not_b_arrow_c_thus_not_b_arrow_c(self):
        # this is an instance of modus ponens
        proof = Tableau(self.logic, parse_argument('NUbc', ['a', 'UaNUbc'])).build()
        assert proof.valid

    def test_valid_bicond_thus_matbicond(self):
        arg = parse_argument('Eab', premises=['Bab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_invalid_matbicon_thus_bicond(self):
        arg = parse_argument('Bab', premises=['Eab'])
        proof = Tableau(self.logic, arg).build()
        assert not proof.valid

    def test_valid_mp_with_neg_bicon(self):
        arg = parse_argument('NBab', premises=['c', 'BcNUab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

class TestGO(LogicTester):

    logic = get_logic('GO')

    def test_truth_table_assertion(self):
        tbl = truth_table(self.logic, 'Assertion')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][2] == 'T'

    def test_truth_table_negation(self):
        tbl = truth_table(self.logic, 'Negation')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'N'
        assert tbl['outputs'][2] == 'F'

    def test_truth_table_disjunction(self):
        tbl = truth_table(self.logic, 'Disjunction')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][2] == 'T'

    def test_truth_table_conjunction(self):
        tbl = truth_table(self.logic, 'Conjunction')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][8] == 'T'

    def test_truth_table_mat_cond(self):
        tbl = truth_table(self.logic, 'Material Conditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'T'
        assert tbl['outputs'][4] == 'F'

    def test_truth_table_mat_bicond(self):
        tbl = truth_table(self.logic, 'Material Biconditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][4] == 'F'

    def test_truth_table_cond(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][3] == 'F'
        assert tbl['outputs'][4] == 'T'

    def test_truth_table_bicond(self):
        tbl = truth_table(self.logic, 'Biconditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][7] == 'F'

    def test_MaterialConditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NCab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('Na'), 'designated': False})
        assert branch.has({'sentence': parse('b'), 'designated': False})

    def test_MaterialBionditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('NEab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('Na'), 'designated': False})
        assert b1.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('a'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConditionalDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('Uab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('ANab'), 'designated': True})
        assert b2.has({'sentence': parse('a'), 'designated': False})
        assert b2.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('NUab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('a'), 'designated': True})
        assert b1.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': True})

    def test_BiconditionalDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Bab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('Uab'), 'designated': True})
        assert branch.has({'sentence': parse('Uba'), 'designated': True})

    def test_BiconditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('NBab'), 'designated': True})
        proof.step()
        b1, b2 = proof.branches
        assert b1.has({'sentence': parse('NUab'), 'designated': True})
        assert b2.has({'sentence': parse('NUba'), 'designated': True})

    def test_AssertionUndesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Ta'), 'designated': False})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_AssertionNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NTa'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_AssertionNegatedUndesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NTa'), 'designated': False})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': True})

    def test_valid_neg_exist_from_univ(self):
        proof = self.example_proof('Quantifier Interdefinability 1')
        assert proof.valid

    def test_valid_neg_univ_from_exist(self):
        proof = self.example_proof('Quantifier Interdefinability 3')
        assert proof.valid

    def test_valid_demorgan_3(self):
        proof = self.example_proof('DeMorgan 3')
        assert proof.valid

    def test_invalid_demorgan_1(self):
        proof = self.example_proof('DeMorgan 1')
        assert not proof.valid

    def test_invalid_exist_from_neg_univ(self):
        proof = self.example_proof('Quantifier Interdefinability 2')
        assert not proof.valid

    def test_invalid_univ_from_neg_exist(self):
        proof = self.example_proof('Quantifier Interdefinability 4')
        assert not proof.valid

    def test_valid_prior_b3e_rule_defect2(self):
        arg = parse_argument('AANaTbNa', premises=['Na'], notn='polish')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_branching_complexity_inherits_branchables(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Kab'), 'designated': False})
        node, = branch.get_nodes()
        assert self.logic.TableauxSystem.branching_complexity(node) == 0


class TestMH(LogicTester):

    logic = get_logic('MH')

    def test_hmh_ax1(self):
        self.assert_axiom('UaUba')

    def test_hmh_ax2(self):
        self.assert_axiom('UUaUbcUUabUac')

    def test_hmh_ax3(self):
        self.assert_axiom('UKaba')

    def test_hmh_ax4(self):
        self.assert_axiom('UKabb')

    def test_hmh_ax5(self):
        self.assert_axiom('UUabUUacUaKbc')

    def test_hmh_ax6(self):
        self.assert_axiom('UaAab')

    def test_hmh_ax7(self):
        self.assert_axiom('UbAab')

    def test_hmh_ax8(self):
        self.assert_axiom('UUacUUbcUAabc')

    def test_hmh_ax9(self):
        self.assert_axiom('BNNaa')

    def test_hmh_ax10(self):
        self.assert_axiom('AAaNaNAaNa')

    def test_hmh_ax11(self):
        self.assert_axiom('AUabNUab')

    def test_hmh_ax12(self):
        self.assert_axiom('UAaNaUUabUNbNa')

    def test_hmh_ax13(self):
        self.assert_axiom('BNKabANaNb')

    def test_hmh_ax14(self):
        self.assert_axiom('BNAabAKNaNbKNAaNaNAbNb')

    def test_hmh_ax15(self):
        self.assert_axiom('UANaNAaNaUab')

    def test_hmh_ax16(self):
        self.assert_axiom('UKaANbNAbNbNUab')

    def test_mp(self):
        proof = self.example_proof('Conditional Modus Ponens')
        assert proof.valid

    def test_inden(self):
        self.assert_axiom('Uaa')

    def test_ifn(self):
        self.assert_axiom('BNAaNaNANaNNa')

    def test_adj(self):
        self.assert_valid('Kab', 'a', 'b')

    def test_p_invalid(self):
        self.assert_invalid('UNbNa', 'NAaNa', 'Uab')

class TestNH(LogicTester):

    logic = get_logic('NH')

    def test_hnh_ax1(self):
        self.assert_axiom('UaUba')

    def test_hnh_ax2(self):
        self.assert_axiom('UUaUbcUUabUac')

    def test_hnh_ax3(self):
        self.assert_axiom('UKaba')

    def test_hnh_ax4(self):
        self.assert_axiom('UKabb')

    def test_hnh_ax5(self):
        self.assert_axiom('UUabUUacUaKbc')

    def test_hnh_ax6(self):
        self.assert_axiom('UaAab')

    def test_hnh_ax7(self):
        self.assert_axiom('UbAab')

    def test_hnh_ax8(self):
        self.assert_axiom('UUacUUbcUAabc')

    def test_hnh_ax9(self):
        self.assert_axiom('BNNaa')

    def test_hnh_ax17(self):
        self.assert_axiom('NKKaNaNKaNa')

    def test_hnh_ax18(self):
        self.assert_axiom('NKUabNUab')

    def test_hnh_ax19(self):
        self.assert_axiom('UNKaNaUUbaUNaNb')

    def test_hnh_ax20(self):
        self.assert_axiom('BKNaNbNAab')

    def test_hnh_ax21(self):
        self.assert_axiom('BANaNbANKabKKaNaKbNb')

    def test_hnh_ax22(self):
        self.assert_axiom('UKNKaNaNaUab')

    def test_hnh_ax23(self):
        self.assert_axiom('UKaKNKbNbNbNUab')

    def test_efq_invalid(self):
        self.assert_invalid('b', 'KaNa')

    def test_lem_valid(self):
        self.assert_valid('AbNb', 'a')

    def test_dem_invalid(self):
        self.assert_invalid('NAab', 'ANaNb')

class TestP3(LogicTester):

    logic = get_logic('P3')

    def test_double_negation_designated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.DoubleNegationDesignated)
        rule.example()
        proof.build()
        assert len(proof.history) == 1
        assert proof.history[0]['rule'] == rule
        assert proof.branches[0].has_all([
            {'sentence': parse('a'), 'designated': False},
            {'sentence': parse('Na'), 'designated': False},
        ])

    def test_conjunction_undesignated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.ConjunctionUndesignated)
        rule.example()
        proof.build()
        assert len(proof.history) == 1
        assert proof.history[0]['rule'] == rule

    def test_material_conditional_designated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.MaterialConditionalDesignated)
        rule.example()
        proof.build()
        assert len(proof.history) > 0
        assert proof.history[0]['rule'] == rule

    def test_universal_negated_designated_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.UniversalNegatedDesignated)
        rule.example()
        proof.build()
        assert len(proof.history) > 0
        assert proof.history[0]['rule'] == rule

    def test_invalid_lem(self):
        proof = self.example_proof('Law of Excluded Middle')
        assert proof.invalid

    def test_invalid_demorgan_1(self):
        proof = self.example_proof('DeMorgan 1')
        assert proof.invalid

    def test_invalid_demorgan_2(self):
        proof = self.example_proof('DeMorgan 2')
        assert proof.invalid

    def test_invalid_demorgan_3(self):
        proof = self.example_proof('DeMorgan 3')
        assert not proof.valid

    def test_invalid_demorgan_4(self):
        proof = self.example_proof('DeMorgan 4')
        assert proof.invalid

    def test_invalid_demorgan_5(self):
        proof = self.example_proof('DeMorgan 5')
        assert proof.invalid

    def test_valid_demorgan_6(self):
        proof = self.example_proof('DeMorgan 6')
        assert proof.valid

class TestCPL(LogicTester):

    logic = get_logic('CPL')

    def test_Closure_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('ContradictionClosure')
        rule.example()
        assert len(proof.branches) == 1

    def test_SelfIdentityClosure_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('SelfIdentityClosure')
        rule.example()
        assert len(proof.branches) == 1

    def test_NonExistenceClosure_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('NonExistenceClosure')
        rule.example()
        assert len(proof.branches) == 1

    def test_IdentityIndiscernability_example(self):
        proof = Tableau(self.logic)
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
        model.read_branch(branch)
        s = Atomic(0, 0)
        assert model.value_of(s) == 'F'
        assert model.value_of(s.negate()) == 'T'

    def test_read_model_extract_disj_2(self):
        proof = self.example_proof('Extracting a Disjunct 2')
        model = self.logic.Model()
        branch = list(proof.open_branches())[0]
        model.read_branch(branch)
        s = Atomic(0, 0)
        assert model.value_of(s) == 'T'
        assert model.value_of(s.negate()) == 'F'

    def test_read_model_no_proof_predicated(self):
        branch = Branch()
        s1 = parse('Fm', vocab=examples.vocabulary)
        branch.add({'sentence': s1})
        model = self.logic.Model()
        model.read_branch(branch)
        assert model.value_of(s1) == 'T'
        
    def test_model_add_access_not_impl(self):
        model = self.logic.Model()
        with pytest.raises(NotImplementedError):
            model.add_access(0, 0)

    def test_model_value_of_operated_opaque(self):
        # coverage
        model = self.logic.Model()
        s = parse('La')
        model.set_opaque_value(s, 'T')
        assert model.value_of_operated(s) == 'T'
        
    def test_model_set_literal_value_predicated1(self):
        model = self.logic.Model()
        m = Constant(0, 0)
        n = Constant(1, 0)
        s = Predicated('Identity', [m, n])
        model.set_literal_value(s, 'T')
        res = model.value_of(s)
        assert res == 'T'

    def test_model_opaque_necessity_branch_make_model(self):
        s = parse('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s})
        model = branch.make_model()
        assert model.value_of(s) == 'T'

    def test_model_opaque_neg_necessity_branch_make_model(self):
        s = parse('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s.negate()})
        model = branch.make_model()
        assert model.value_of(s) == 'F'

    def test_model_get_data_triv(self):
        s = parse('a')
        model = self.logic.Model()
        model.set_literal_value(s, 'T')
        model.finish()
        data = model.get_data()
        assert 'Atomics' in data

    def test_identity_indiscernability_not_applies(self):
        vocab = Vocabulary()
        vocab.declare_predicate('MyPred', 0, 0, 2)
        proof = Tableau(self.logic)
        s1 = parse('Fmn', vocab=vocab)
        s2 = parse('Io1o2')
        branch = proof.branch()
        branch.update([
            {'sentence': s1, 'world': 0},
            {'sentence': s2, 'world': 0},
        ])
        rule = proof.get_rule(proof.logic.TableauxRules.IdentityIndiscernability)
        assert not rule.get_target(branch)

    def test_model_value_of_operated_opaque1(self):
        s1 = parse('La')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'F')
        res = model.value_of_operated(s1.negate())
        assert res == 'T'

    def test_model_value_of_opaque_unassigned(self):
        s = parse('La')
        model = self.logic.Model()
        res = model.value_of(s)
        assert res == model.unassigned_value

    def test_model_set_predicated_false_value_error_on_set_to_true(self):
        s = parse('Fm', vocab=examples.vocabulary)
        model = self.logic.Model()
        model.set_literal_value(s, 'F')
        with pytest.raises(ModelValueError):
            model.set_literal_value(s, 'T')

    def test_model_get_anti_extension(self):
        # coverage
        s = parse('Fm', vocab=examples.vocabulary)
        model = self.logic.Model()
        predicate = s.predicate
        anti_extension = model.get_anti_extension(predicate)
        assert len(anti_extension) == 0
        model.set_literal_value(s, 'F')
        assert tuple(s.parameters) in anti_extension

    def test_group_score_from_candidate_score1(self):
        arg = parse_argument('Na', premises=['Cab', 'Nb', 'Acd'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid
        assert len(proof.branches) == 2

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
        model.set_literal_value(s, 'T')
        model.finish()
        data = model.get_data()
        assert 'Atomics' in data

    def test_model_value_of_operated_opaque1(self):
        s1 = parse('La')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'F')
        res = model.value_of_operated(s1.negate())
        assert res == 'T'

    def test_model_value_of_operated_opaque2(self):
        s1 = parse('La')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'T')
        res = model.value_of_operated(s1)
        assert res == 'T'

    def test_model_read_node_opaque(self):
        s1 = parse('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s1})
        model = self.logic.Model()
        model.read_node(branch.nodes[0])
        assert model.value_of(s1) == 'T'

    def test_model_add_access_not_impl(self):
        model = self.logic.Model()
        with pytest.raises(NotImplementedError):
            model.add_access(0, 0)

    def test_model_read_branch_with_negated_opaque_then_faithful(self):
        arg = parse_argument('a', premises=['NLa', 'b'])
        proof = Tableau(self.logic, arg, is_build_models=True)
        proof.build()
        model = proof.branches[0].model
        assert model.value_of(parse('a'))   == 'F'
        assert model.value_of(parse('La'))  == 'F'
        assert model.value_of(parse('NLa')) == 'T'
        assert model.is_countermodel_to(arg)

    def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
        vocab = Vocabulary((('Pred', 0, 0, 1),))
        proof = Tableau(self.logic, parse_argument('b', premises=['VxKFxKaNa'], vocab=vocab))
        proof.build()
        assert proof.valid

    def test_invalid_existential_inside_univ_max_steps(self):
        arg = parse_argument('b', ['VxUFxSyFy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(max_steps=100)
        assert proof.invalid

    def test_quantified_opaque_is_countermodel(self):
        # for this we needed to add constants that occur within opaque sentences.
        # the use of the existential is important given the way the K model
        # computes quantified values (short-circuit), as opposed to FDE (min/max).
        arg = parse_argument('b', ['SxUNFxSyMFy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg, is_build_models=True)
        proof.build()
        # this assert is so our test has integrity
        assert len(proof.branches) == 2
        assert proof.branches[0].model.is_countermodel_to(arg)
        assert proof.branches[1].model.is_countermodel_to(arg)

    def test_model_identity_predication1(self):
        model = self.logic.Model()
        s1 = parse('Fm', vocab=self.vocab)
        s2 = parse('Imn')
        s3 = parse('Fn', vocab=self.vocab)
        model.set_literal_value(s1, 'T')
        model.set_literal_value(s2, 'T')
        model.finish()
        assert model.value_of(s3) == 'T'

    def test_model_identity_predication2(self):
        model = self.logic.Model()
        s1 = parse('Fm', vocab=self.vocab)
        s2 = parse('Inm')
        s3 = parse('Fn', vocab=self.vocab)
        model.set_literal_value(s1, 'T')
        model.set_literal_value(s2, 'T')
        model.finish()
        assert model.value_of(s3) == 'T'

    def test_model_self_identity1(self):
        model = self.logic.Model()
        # here we make sure the constant m is registered
        s1 = self.p('Fm')
        model.set_literal_value(s1, 'F')
        model.finish()
        s2 = self.p('Imm')
        assert model.value_of(s2) == 'T'

    def test_model_raises_denotation_error(self):
        model = self.logic.Model()
        model.finish()
        s1 = self.p('Imm')
        with pytest.raises(DenotationError):
            model.value_of(s1)

    def test_model_get_identicals_singleton_two_identical_constants(self):
        model = self.logic.Model()
        s1 = self.p('Imn')
        c1, c2 = s1.parameters
        model.set_literal_value(s1, 'T')
        model.finish()
        identicals = model.get_identicals(c1)
        assert len(identicals) == 1
        assert c2 in identicals

    def test_model_singleton_domain_two_identical_constants(self):
        model = self.logic.Model()
        s1 = self.p('Imn')
        model.set_literal_value(s1, 'T')
        model.finish()
        d = model.get_domain()
        assert len(d) == 1

    def test_model_same_denotum_two_identical_constants(self):
        model = self.logic.Model()
        s1 = self.p('Imn')
        c1, c2 = s1.parameters
        model.set_literal_value(s1, 'T')
        model.finish()
        d1 = model.get_denotum(c1)
        d2 = model.get_denotum(c2)
        assert d1 is d2

class TestK(LogicTester):

    logic = get_logic('K')

    def test_ContradictionClosure_example(self):
        rule = self.logic.TableauxRules.ContradictionClosure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_SelfIdentityClosure_example(self):
        rule = self.logic.TableauxRules.SelfIdentityClosure(empty_proof())
        rule.example()
        assert len(rule.tableau.branches) == 1

    def test_Possibility_example_node(self):
        rule = self.logic.TableauxRules.Possibility(empty_proof())
        props = rule.example_node(rule.branch())
        assert props['world'] == 0

    def test_Existential_example_node(self):
        rule = self.logic.TableauxRules.Existential(empty_proof())
        props = rule.example_node(rule.branch())
        assert props['sentence'].quantifier == 'Existential'

    def test_DisjunctionNegated_example_node(self):
        rule = self.logic.TableauxRules.DisjunctionNegated(empty_proof())
        props = rule.example_node(rule.branch())
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
        branch.add({'sentence': parse('Fs', vocab=examples.vocabulary), 'world': 0})
        rule = self.logic.TableauxRules.IdentityIndiscernability(proof)
        res = rule.get_target(branch)
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
        proof = self.example_proof('Necessity Distribution 1')
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
        proof = self.example_proof('Necessity Distribution 1')
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

    def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
        vocab = Vocabulary((('Pred', 0, 0, 1),))
        proof = Tableau(self.logic, parse_argument('b', premises=['VxKFxKaNa'], vocab=vocab))
        proof.build()
        assert proof.valid

    def test_read_model_proof_deny_antec(self):
        proof = self.example_proof('Denying the Antecedent')
        model = self.logic.Model()
        branch = list(proof.open_branches())[0]
        model.read_branch(branch)
        s = Atomic(0, 0)
        assert model.value_of(s, world=0) == 'F'
        assert model.value_of(s.negate(), world=0) == 'T'

    def test_read_model_no_proof_atomic(self):
        model = self.logic.Model()
        branch = Branch()
        branch.add({'sentence': Atomic(0, 0), 'world': 0})
        model.read_branch(branch)
        assert model.value_of(Atomic(0, 0), world=0) == 'T'

    def test_read_model_no_proof_predicated(self):
        model = self.logic.Model()
        branch = Branch()
        s1 = parse('Imn')
        branch.add({'sentence': s1, 'world': 0})
        model.read_branch(branch)
        assert model.value_of(s1, world=0) == 'T'

    def test_read_model_no_proof_access(self):
        model = self.logic.Model()
        branch = Branch()
        branch.add({'world1': 0, 'world2': 1})
        model.read_branch(branch)
        assert model.has_access(0, 1)

    def test_model_value_of_atomic_unassigned(self):
        model = self.logic.Model()
        s = Atomic(0, 0)
        res = model.value_of_atomic(s, 'F')
        assert res == model.unassigned_value

    def test_model_set_predicated_value1(self):
        model = self.logic.Model()
        m = Constant(0, 0)
        n = Constant(1, 0)
        s = Predicated('Identity', [m, n])
        model.set_predicated_value(s, 'T', world=0)
        res = model.value_of(s, world=0)
        assert res == 'T'

    def test_model_add_access_sees(self):
        model = self.logic.Model()
        model.add_access(0, 0)
        assert 0 in model.visibles(0)

    def test_model_possibly_a_with_access_true(self):
        model = self.logic.Model()
        a = Atomic(0, 0)
        model.add_access(0, 1)
        model.set_atomic_value(a, 'T', world=1)
        res = model.value_of(Operated('Possibility', [a]), world=0)
        assert res == 'T'

    def test_model_possibly_a_no_access_false(self):
        model = self.logic.Model()
        a = Atomic(0, 0)
        model.set_atomic_value(a, 'T', world=1)
        res = model.value_of(Operated('Possibility', [a]), world=0)
        assert res == 'F'

    def test_model_nec_a_no_access_true(self):
        model = self.logic.Model()
        a = Atomic(0, 0)
        res = model.value_of(Operated('Necessity', [a]), world=0)
        assert res == 'T'

    def test_model_nec_a_with_access_false(self):
        model = self.logic.Model()
        a = Atomic(0, 0)
        model.set_atomic_value(a, 'T', world=0)
        model.set_atomic_value(a, 'F', world=1)
        model.add_access(0, 1)
        model.add_access(0, 0)
        res = model.value_of(Operated('Necessity', [a]), world=0)
        assert res == 'F'

    def test_model_existence_user_pred_true(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1 = Predicated('MyPred', [m], v)
        s2 = Predicated('MyPred', [x], v)
        s3 = Quantified('Existential', x, s2)

        model = self.logic.Model()
        model.set_predicated_value(s1, 'T', world=0)
        res = model.value_of(s3, world=0)
        assert res == 'T'

    def test_model_existense_user_pred_false(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1 = Predicated('MyPred', [m], v)
        s2 = Predicated('MyPred', [x], v)
        s3 = Quantified('Existential', x, s2)

        model = self.logic.Model()
        res = model.value_of(s3, world=0)
        assert res == 'F'

    def test_model_universal_user_pred_true(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = Constant(0, 0)
        x = Variable(0, 0)
        s1 = Predicated('MyPred', [m], v)
        s2 = Predicated('MyPred', [x], v)
        s3 = Quantified('Universal', x, s2)

        model = self.logic.Model()
        model.set_predicated_value(s1, 'T', world=0)
        res = model.value_of(s3, world=0)
        assert res == 'T'

    def test_model_universal_false(self):
        s1 = parse('VxFx', vocab=examples.vocabulary)
        s2 = parse('Fm', vocab=examples.vocabulary)
        model = self.logic.Model()
        model.set_predicated_value(s2, 0, world=0)
        res = model.value_of(s1, world=0)
        assert res == 'F'

    def test_model_universal_user_pred_false(self):
        v = Vocabulary()
        v.declare_predicate('MyPred', 0, 0, 1)
        m = Constant(0, 0)
        n = Constant(1, 0)
        x = Variable(0, 0)
        s1 = Predicated('MyPred', [m], v)
        s2 = Predicated('MyPred', [x], v)
        s3 = Predicated('MyPred', [n], v)
        s4 = Quantified('Universal', x, s2)
    
        model = self.logic.Model()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s3, 'F', world=0)
        res = model.value_of(s4, world=0)
        assert res == 'F'

    def test_model_identity_extension_non_empty_with_sentence(self):
        s = parse('Imn')
        model = self.logic.Model()
        model.set_predicated_value(s, 'T', world=0)
        extension = model.get_extension(get_system_predicate('Identity'), world=0)
        assert len(extension) > 0
        assert (Constant(0, 0), Constant(1, 0)) in extension
        
    def test_model_frame_data_has_identity_with_sentence(self):
        s = parse('Imn')
        model = self.logic.Model()
        model.set_predicated_value(s, 'T', world=0)
        model.finish()
        data = model.get_data()
        assert len(data['Frames']['values']) == 1
        fdata = data['Frames']['values'][0]['value']
        assert len(fdata['Predicates']['values']) == 2
        pdata = fdata['Predicates']['values'][1]
        assert pdata['values'][0]['input'].name == 'Identity'

    def test_model_get_data_with_access_has_2_frames(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'T', world=0)
        model.add_access(0, 1)
        model.finish()
        data = model.get_data()
        assert len(data['Frames']['values']) == 2

    def test_frame_difference_atomic_keys_diff(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'T', world=0)
        model.set_literal_value(parse('b'), 'T', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert not frame_a.is_equivalent_to(frame_b)
        assert not frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_atomic_values_diff(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'T', world=0)
        model.set_literal_value(parse('a'), 'F', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert not frame_a.is_equivalent_to(frame_b)
        assert not frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_atomic_values_equiv(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'T', world=0)
        model.set_literal_value(parse('a'), 'T', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert frame_a.is_equivalent_to(frame_b)
        assert frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_opaque_keys_diff(self):
        model = self.logic.Model()
        model.set_opaque_value(parse('Ma'), 'T', world=0)
        model.set_opaque_value(parse('Mb'), 'T', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert not frame_a.is_equivalent_to(frame_b)
        assert not frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_opaque_values_diff(self):
        model = self.logic.Model()
        model.set_opaque_value(parse('Ma'), 'T', world=0)
        model.set_opaque_value(parse('Ma'), 'F', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert not frame_a.is_equivalent_to(frame_b)
        assert not frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_opaque_values_equiv(self):
        model = self.logic.Model()
        model.set_opaque_value(parse('Ma'), 'T', world=0)
        model.set_opaque_value(parse('Ma'), 'T', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert frame_a.is_equivalent_to(frame_b)
        assert frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_extension_keys_diff(self):
        vocab = Vocabulary()
        vocab.add_predicate(examples.vocabulary.get_predicate(index=0, subscript=0))
        vocab.declare_predicate('g', 1, 0, 2)
        s1 = parse('Fm', vocab=vocab)
        s2 = parse('Gmn', vocab=vocab)
        model = self.logic.Model()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s2, 'T', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert not frame_a.is_equivalent_to(frame_b)
        assert not frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_extension_values_diff(self):
        s1 = parse('Fm', vocab=examples.vocabulary)
        s2 = parse('Fn', vocab=examples.vocabulary)
        model = self.logic.Model()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s2, 'T', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert not frame_a.is_equivalent_to(frame_b)
        assert not frame_b.is_equivalent_to(frame_a)

    def test_frame_difference_extension_values_equiv(self):
        s1 = parse('Fm', vocab=examples.vocabulary)
        s2 = parse('Fn', vocab=examples.vocabulary)
        model = self.logic.Model()
        model.set_predicated_value(s1, 'T', world=0)
        model.set_predicated_value(s2, 'F', world=0)
        model.set_predicated_value(s1, 'T', world=1)
        model.set_predicated_value(s2, 'F', world=1)
        frame_a = model.world_frame(0)
        frame_b = model.world_frame(1)
        assert frame_a.is_equivalent_to(frame_b)
        assert frame_b.is_equivalent_to(frame_a)

    def test_frame_not_equals(self):
        s = parse('a')
        model1 = self.logic.Model()
        model2 = self.logic.Model()
        model1.set_literal_value(s, 'T', world=0)
        model2.set_literal_value(s, 'F', world=0)
        f1 = model1.world_frame(0)
        f2 = model2.world_frame(0)
        assert f1 != f2

    def test_frame_not_equals(self):
        s = parse('a')
        model1 = self.logic.Model()
        model2 = self.logic.Model()
        model1.set_literal_value(s, 'T', world=0)
        model2.set_literal_value(s, 'T', world=0)
        f1 = model1.world_frame(0)
        f2 = model2.world_frame(0)
        assert f1 == f2

    def test_frame_ordering(self):
        s = parse('a')
        model = self.logic.Model()
        model.set_literal_value(s, 'T', world=0)
        model.set_literal_value(s, 'F', world=1)
        f1 = model.world_frame(0)
        f2 = model.world_frame(1)
        assert f2 > f1
        assert f1 < f2
        assert f2 >= f1
        assert f1 <= f2
        # coverage
        assert f1.__cmp__(f2) < 0

    def test_model_not_impl_various(self):
        s1 = parse('Aab')
        model = self.logic.Model()
        with pytest.raises(NotImplementedError):
            model.set_literal_value(s1, 'T')
        with pytest.raises(NotImplementedError):
            model.value_of_modal(s1)
        with pytest.raises(NotImplementedError):
            model.value_of_quantified(s1)

    def test_model_value_error_various(self):
        s1 = parse('a')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'T')
        with pytest.raises(ModelValueError):
            model.set_opaque_value(s1, 'F')
        model = self.logic.Model()
        model.set_atomic_value(s1, 'T')
        with pytest.raises(ModelValueError):
            model.set_atomic_value(s1, 'F')
        s2 = parse('Fm', vocab=examples.vocabulary)
        model.set_predicated_value(s2, 'T')
        with pytest.raises(ModelValueError):
            model.set_predicated_value(s2, 'F')

    def test_model_get_extension_adds_predicate_to_predicates(self):
        # coverage
        s1 = parse('Fm', vocab=examples.vocabulary)
        model = self.logic.Model()
        res = model.get_extension(s1.predicate)
        assert len(res) == 0
        assert s1.predicate in model.predicates

    def test_model_is_countermodel_to_false1(self):
        arg = parse_argument('b', premises=['a'])
        s1 = arg.premises[0]
        model = self.logic.Model()
        model.set_literal_value(s1, 'F')
        model.set_literal_value(arg.conclusion, 'T')
        assert not model.is_countermodel_to(arg)

    def test_nonexistence_closure1(self):
        arg = parse_argument('b', premises=['NJm'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_nonexistence_closure_example(self):
        proof = Tableau(self.logic, None)
        rule = proof.get_rule(self.logic.TableauxRules.NonExistenceClosure)
        rule.example()
        proof.build()
        assert proof.valid

    def test_invalid_s4_cond_inf_2(self):
        proof = self.example_proof('S4 Conditional Inference 2')
        assert not proof.valid

    def test_model_finish_every_opaque_has_value_in_every_frame(self):
        s1 = parse('a')
        s2 = parse('b')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'T', world=0)
        model.set_opaque_value(s2, 'T', world=1)
        model.finish()
        f1 = model.world_frame(0)
        f2 = model.world_frame(1)
        assert s2 in f1.opaques
        assert s1 in f2.opaques

    def test_universal_should_make_new_constant_with_one_there(self):

        # see commit 8889b92 for bug fix

        vocab = examples.vocabulary

        s1 = parsex('VxUFxSyGy')
        s2 = parsex('b')

        s3 = parsex('NFm')

        proof = Tableau(self.logic, parse_argument(s2, [s1]))
        
        univ = proof.get_rule('Universal')
        b1 = proof.branches[0]

        ap1 = proof.step()
        assert ap1['rule'].name == 'Universal'

        ap2 = proof.step()
        assert ap2['rule'].name == 'Conditional'
        assert b1.has({'sentence': s3, 'world': 0})
        b2 = proof.branches[1]

        # we don't apply now
        assert not univ.get_target(b1)

        # do some steps, but NOT on our b1
        for i in range(10):
            opens = {b for b in proof.open_branches() if b != b1}
            for b in opens:
                res = proof.get_branch_application(b)
                if res:
                    rule, target = res
                    proof.do_application(rule, target, None)
                    break

        # we shouldn't apply now
        target = univ.get_target(b1)
        assert not target , target['sentence']

    def test_nested_diamond_within_box1(self):
        arg = parse_argument('KMNbc', ['LCaMNb', 'Ma'])
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.invalid

    def test_invalid_existential_inside_univ_max_steps(self):
        arg = parse_argument('b', ['VxUFxSyFy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(max_steps=100)
        assert proof.invalid

class TestD(LogicTester):

    logic = get_logic('D')

    def test_Serial_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('Serial')
        rule.example()
        assert len(proof.branches) == 1

    def test_Serial_not_applies_to_branch_empty(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        rule = proof.get_rule('Serial')
        res = rule.get_target(branch)
        assert not res

    def test_valid_serial_inf_1(self):
        proof = self.example_proof('Serial Inference 1')
        assert proof.valid

    def test_invalid_reflex_inf_1(self):
        proof = self.example_proof('Reflexive Inference 1')
        assert not proof.valid

    def test_invalid_optimize_nec_rule1_max_steps_50(self):
        arg = parse_argument('NLVxNFx', premises=['LMSxFx'], vocab=examples.vocabulary)
        proof = Tableau(self.logic, arg)
        proof.build(max_steps=50)
        assert proof.invalid

    def test_invalid_s4_cond_inf_2(self):
        proof = self.example_proof('S4 Conditional Inference 2')
        assert not proof.valid

    def test_valid_long_serial_max_steps_50(self):
        proof = Tableau(self.logic, parse_argument('MMMMMa', premises=['LLLLLa']))
        proof.build(max_steps=50)
        assert proof.valid

    def test_verify_core_bugfix_branch_should_not_have_w1_with_more_than_one_w2(self):
        proof = Tableau(self.logic, parse_argument('CaLMa'))
        proof.build()

        # sanity check
        assert len(proof.branches) == 1

        branch = proof.branches[0]

        # use internal properties just to be sure, since the bug was with the .find method
        access = {}
        for node in list(branch.nodes):
            if 'world1' in node.props:
                w1 = node.props['world1']
                w2 = node.props['world2']
                if w1 not in access:
                    # use a list to also make sure we don't have redundant nodes
                    access[w1] = list()
                access[w1].append(w2)
        
        for w1 in access:
            assert len(access[w1]) == 1
        assert len(access) == (len(branch.worlds()) - 1)

        # sanity check
        assert len(branch.worlds()) > 2
            
        
class TestT(LogicTester):

    logic = get_logic('T')

    def test_Reflexive_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.Reflexive)
        rule.example()
        proof.build()
        branch = proof.branches[0]
        assert branch.has({'world1': 0, 'world2': 0})

    def test_valid_np_collapse_1(self):
        proof = self.example_proof('NP Collapse 1')
        assert proof.valid

    def test_invalid_s4_material_inf_1(self):
        proof = self.example_proof('S4 Material Inference 1')
        assert proof.invalid

    def test_valid_optimize_nec_rule1(self):
        arg = parse_argument('NLVxNFx', ['LMSxFx'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(build_timeout=1000)
        assert proof.valid

    def test_invalid_s4_cond_inf_2(self):
        proof = self.example_proof('S4 Conditional Inference 2')
        assert proof.invalid

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):
        #
        # Rule ordering benchmark result:
        #
        #          [# non-branching rules]
        #                [S4:Transitive]
        #          [Necessity, Possibility]
        #                [T:Reflexive]
        #          [# branching rules]
        #        - [Existential, Universal]
        #                [S5:Symmetric]
        #            [D:Serial],
        #      S5: 8 branches, 142 steps
        #      S4: 8 branches, 132 steps
        #       T: 8 branches, 91 steps
        #       D: 8 branches, 57 steps
        # 
        arg = parse_argument('b', ['LVxSyUFxLMGy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        # 200 might be agressive
        proof.build(max_steps=200)
        assert proof.invalid

class TestS4(LogicTester):

    logic = get_logic('S4')

    def test_Transitive_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule('Transitive')
        rule.example()
        proof.build()
        branch = proof.branches[0]
        assert branch.has({'world1': 0, 'world2': 2})

    def test_valid_s4_material_inf_1(self):
        proof = self.example_proof('S4 Material Inference 1')
        assert proof.valid

    def test_valid_np_collapse_1(self):
        proof = self.example_proof('NP Collapse 1')
        assert proof.valid

    def test_invalid_s5_cond_inf_1(self):
        proof = self.example_proof('S5 Conditional Inference 1')
        assert proof.invalid

    def test_valid_optimize_nec_rule1(self):
        arg = parse_argument('NLVxNFx', ['LMSxFx'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        proof.build(build_timeout=1000)
        assert proof.valid

    def test_model_finish_transitity_visibles(self):
        model = self.logic.Model()
        model.add_access(0, 1)
        model.add_access(1, 2)
        model.finish()
        assert 2 in model.visibles(0)

    def test_valid_s4_cond_inf_2(self):
        proof = self.example_proof('S4 Conditional Inference 2')
        assert proof.valid

    def test_invalid_problematic_1_with_timeout(self):
        proof = Tableau(self.logic, parse_argument('b', premises=['LMa']))
        proof.build(build_timeout=2000)
        assert not proof.valid

    def test_valid_s4_complex_possibility_with_max_steps(self):
        proof = Tableau(self.logic, parse_argument('MNb', premises=['LCaMMMNb', 'Ma']))
        proof.build(max_steps=200)
        assert proof.valid

    def test_nested_diamond_within_box1(self):
        arg = parse_argument('KMNbc', ['LCaMNb', 'Ma'])
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.invalid

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):
        #
        # Rule ordering benchmark result:
        #
        #          [# non-branching rules]
        #                [S4:Transitive]
        #          [Necessity, Possibility]
        #                [T:Reflexive]
        #          [# branching rules]
        #        - [Existential, Universal]
        #                [S5:Symmetric]
        #            [D:Serial],
        #      S5: 8 branches, 142 steps
        #      S4: 8 branches, 132 steps
        #       T: 8 branches, 91 steps
        #       D: 8 branches, 57 steps
        # 
        arg = parse_argument('b', ['LVxSyUFxLMGy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        # 200 might be agressive
        proof.build(max_steps=200)
        assert proof.invalid

class TestS5(LogicTester):

    logic = get_logic('S5')

    def test_Symmetric_example(self):
        proof = Tableau(self.logic)
        rule = proof.get_rule(self.logic.TableauxRules.Symmetric)
        rule.example()
        proof.build()
        branch = proof.branches[0]
        assert branch.has({'world1': 1, 'world2': 0})

    def test_valid_s4_cond_inf_2(self):
        proof = self.example_proof('S4 Conditional Inference 2')
        assert proof.valid

    def test_valid_s5_cond_inf_1(self):
        proof = self.example_proof('S5 Conditional Inference 1')
        assert proof.valid

    def test_model_finish_symmetry_visibles(self):
        model = self.logic.Model()
        model.add_access(0, 1)
        model.finish()
        assert 0 in model.visibles(1)

    def test_valid_s4_complex_possibility_with_max_steps(self):
        proof = Tableau(self.logic, parse_argument('MNb', premises=['LCaMMMNb', 'Ma']))
        proof.build(max_steps=200)
        assert proof.valid

    def test_nested_diamond_within_box1(self):
        arg = parse_argument('KMNbc', ['LCaMNb', 'Ma'])
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.invalid

    def test_valid_optimize_nec_rule1(self):
        arg = parse_argument('NLVxNFx', premises=['LMSxFx'], notn='polish', vocab=examples.vocabulary)
        proof = Tableau(self.logic, arg)
        proof.build(build_timeout=1000)
        assert proof.valid

    def test_intermediate_mix_modal_quantifiers1(self):
        # For this we needed to put Universal and Existential rules
        # in the same group, and toward the end.
        vocab = Vocabulary([
            ('PredF', 0, 0, 1),
            ('PredG', 1, 0, 1),
        ])
        arg = parse_argument('MSxGx', ['VxLSyUFxMGy', 'Fm'], vocab=vocab)
        proof = Tableau(self.logic, arg)
        proof.build(max_steps=100)
        assert proof.valid

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):
        #
        # Rule ordering benchmark result:
        #
        #          [# non-branching rules]
        #                [S4:Transitive]
        #          [Necessity, Possibility]
        #                [T:Reflexive]
        #          [# branching rules]
        #        - [Existential, Universal]
        #                [S5:Symmetric]
        #            [D:Serial],
        #      S5: 8 branches, 142 steps
        #      S4: 8 branches, 132 steps
        #       T: 8 branches, 91 steps
        #       D: 8 branches, 57 steps
        # 
        arg = parse_argument('b', ['LVxSyUFxLMGy'], vocab=self.vocab)
        proof = Tableau(self.logic, arg)
        # 200 might be agressive
        proof.build(max_steps=200)
        assert proof.invalid
        
class TestMaxConstantsTracker(LogicTester):

    logic = get_logic('S5')

    class MockRule(FilterNodeRule):

        def setup(self):
            self.add_helper('mtr', MaxConstantsTracker(self))

    Rule = MockRule

    def test_argument_trunk_two_qs_returns_3(self):
        arg = parse_argument('NLVxNFx', ['LMSxFx'], vocab=self.vocab)
        proof = Tableau(self.logic)
        proof.add_rule_group([self.Rule])
        proof.set_argument(arg)
        rule = proof.get_rule(self.Rule)
        branch = proof.branches[0]
        assert rule.mtr._compute_max_constants(branch) == 3

    def compute_for_node_one_q_returns_1(self):
        s =  parse('LxFx', vocab=self.vocab)
        n = {'sentence': s, 'world': 0}
        node = Node(n)
        proof = Tableau(None)
        rule = Rule(proof)
        branch = proof.branch()
        branch.add(node)
        res = rule.mtr._compute_needed_constants_for_node(node, branch)
        assert res == 1

    def compute_for_branch_two_nodes_one_q_each_returns_3(self):
        s1 = parse('LxFx', vocab=self.vocab)
        s2 = parse('SxFx', vocab=self.vocab)
        n1 = {'sentence': s1, 'world': 0}
        n2 = {'sentence': s2, 'world': 0}
        proof = Tableau(None)
        rule = Rule(proof)
        branch = proof.branch()
        branch.update([n1, n2])
        res = rule.mtr._compute_max_constants(branch)
        assert res == 3