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
# pytableaux - core logic test cases
import pytest

import logic
import examples
import time

def test_parse_standard():
    s = logic.parse('A & B', notation='standard')
    assert s.is_operated
    assert s.operator == 'Conjunction'

def test_parse_polish():
    s = logic.parse('Kab', notation='polish')
    assert s.is_operated
    assert s.operator == 'Conjunction'

def test_argument_no_prems_1_std_untitled():
    a = logic.argument(conclusion='A', notation='standard')
    assert len(a.premises) == 0
    assert a.conclusion.is_atomic()

def test_argument_prems_preparsed_titled():
    premises = [logic.parse('Aab'), logic.parse('Nb')]
    conclusion = logic.parse('a')
    a = logic.argument(conclusion=conclusion, premises=premises, title='TestArgument')
    assert len(a.premises) == 2
    assert a.title == 'TestArgument'

def test_argument_parse_prems_preparsed_conclusion():
    premises = ['Aab', 'Nb']
    conclusion = logic.parse('a')
    a = logic.argument(conclusion=conclusion, premises=premises, notation='polish')
    assert len(a.premises) == 2
    assert a.conclusion == conclusion

def test_argument_repr_untitled():
    a = logic.argument(conclusion='a', notation='polish')
    res = a.__repr__()
    assert 'title' not in res

def test_argument_repr_titled():
    a = logic.argument(conclusion='a', notation='polish', title='TestArg')
    res = a.__repr__()
    assert 'title' in res

def test_truth_table_cpl_negation():
    tbl = logic.truth_table('cpl', 'Negation')
    assert len(tbl['inputs']) == 2
    assert len(tbl['outputs']) == 2
    assert tbl['inputs'][0][0] == 'F'
    assert tbl['outputs'][0] == 'T'

def test_truth_tables_cpl():
    tbls = logic.truth_tables('cpl')
    assert tbls['Negation']['outputs'][0] == 'T'

def test_get_logic_cpl_case_insensitive():
    lgc1 = logic.get_logic('cpl')
    lgc2 = logic.get_logic('CPL')
    assert lgc1 == lgc2

def test_get_logic_none_bad_argument():
    with pytest.raises(logic.BadArgumentError):
        logic.get_logic(None)

class TestVocabulary(object):

    def test_predicate_error_pred_defs_duple(self):
        with pytest.raises(logic.Vocabulary.PredicateError):
            logic.Vocabulary(predicate_defs=[('foo', 4)])

    def test_get_predicate_by_name_sys_identity(self):
        v = logic.Vocabulary()
        p = v.get_predicate('Identity')
        assert p.name == 'Identity'

    def test_get_predicate_by_index_subscript_sys_identity(self):
        v = logic.Vocabulary()
        p = v.get_predicate(-1, subscript=0)
        # TODO: after refactor test for get_predicate(-1, 0)
        assert p.name == 'Identity'

    def test_get_predicate_no_such_predicate_error_bad_name(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            v.get_predicate('NonExistentPredicate')

    def test_get_predicate_no_such_predicate_error_bad_custom_index(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            v.get_predicate(index=1, subscript=2)

    def test_get_predicate_no_such_predicate_error_bad_sys_index(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            v.get_predicate(index=-1, subscript=2)

    def test_get_predicate_no_such_predicate_error_not_enough_info(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateError):
            v.get_predicate(index=-1)

    def test_declare_predicate1(self):
        v = logic.Vocabulary()
        p = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert p.name == 'MyPredicate'
        assert p.index == 0
        assert p.subscript == 0
        assert p.arity == 1

    def test_vocab_copy_get_predicate(self):
        v = logic.Vocabulary()
        predicate = v.declare_predicate('MyPredicate', 0, 0, 1)
        v2 = v.copy()
        assert v2.get_predicate('MyPredicate') == predicate

    def test_python2_cmp_self_0(self):
        v = logic.Vocabulary()
        predicate = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert predicate.__cmp__(predicate) == 0

    def test_add_predicate_raises_non_predicate(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateError):
            v.add_predicate('foo')

    def test_add_predicate_raises_sys_predicate(self):
        v = logic.Vocabulary()
        pred = logic.get_system_predicate('Identity')
        with pytest.raises(logic.Vocabulary.PredicateError):
            v.add_predicate(pred)

    def test_declare_predicate_already_declared_sys(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateAlreadyDeclaredError):
            v.declare_predicate('Identity', 0, 0, 2)

    def test_declare_predicate_already_declared_user_name(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        with pytest.raises(logic.Vocabulary.PredicateAlreadyDeclaredError):
            v.declare_predicate('MyPredicate', 0, 0, 1)

    def test_declare_predicate_already_declared_user_index_subscript(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        with pytest.raises(logic.Vocabulary.PredicateAlreadyDeclaredError):
            v.declare_predicate('MyPredicate2', 0, 0, 1)

    def test_declare_predicate_index_too_large(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.IndexTooLargeError):
            v.declare_predicate('MyPredicate', logic.num_predicate_symbols, 0, 1)

    def test_declare_predicate_arity_non_int(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateArityError):
            v.declare_predicate('MyPredicate', 0, 0, None)

    def test_declare_predicate_arity_0_error(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateArityError):
            v.declare_predicate('MyPredicate', 0, 0, 0)

    def test_new_predicate_subscript_non_int(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateSubscriptError):
            logic.Vocabulary.Predicate('MyPredicate', 0, None, 1)

    def test_new_predicate_subscript_less_than_0_error(self):
        with pytest.raises(logic.Vocabulary.PredicateSubscriptError):
            logic.Vocabulary.Predicate('MyPredicate', 0, -1, 1)

    def test_predicate_is_system_predicate_true(self):
        assert logic.get_system_predicate('Identity').is_system_predicate()

    def test_predicate_eq_true(self):
        assert logic.get_system_predicate('Identity') == logic.get_system_predicate('Identity')

    def test_predicate_system_less_than_user(self):
        v = logic.Vocabulary()
        predicate = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert logic.get_system_predicate('Identity') < predicate

    def test_predicate_system_less_than_or_equal_to_user(self):
        v = logic.Vocabulary()
        predicate = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert logic.get_system_predicate('Identity') <= predicate

    def test_predicate_user_greater_than_system(self):
        v = logic.Vocabulary()
        predicate = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert predicate > logic.get_system_predicate('Identity')

    def test_predicate_user_greater_than_or_equal_to_system(self):
        v = logic.Vocabulary()
        predicate = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert predicate >= logic.get_system_predicate('Identity')

    def test_list_predicates_contains_identity(self):
        v = logic.Vocabulary()
        names = v.list_predicates()
        assert 'Identity' in names

    def test_list_predicates_contains_user_pred(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        names = v.list_predicates()
        assert 'MyPredicate' in names

    def test_list_user_predicates_contains_user_pred(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        names = v.list_user_predicates()
        assert 'MyPredicate' in names

    def test_list_user_predicates_not_contains_sys(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        names = v.list_user_predicates()
        assert 'Identity' not in names

    def test_constant_index_too_large(self):
        with pytest.raises(logic.Vocabulary.IndexTooLargeError):
            logic.constant(logic.num_const_symbols, 0)

    def test_constant_is_constant_not_variable(self):
        c = logic.constant(0, 0)
        assert c.is_constant()
        assert not c.is_variable()

    def test_variable_index_too_large(self):
        with pytest.raises(logic.Vocabulary.IndexTooLargeError):
            logic.variable(logic.num_var_symbols, 0)

    def test_sentence_is_sentence(self):
        s = logic.parse('a')
        assert s.is_sentence()

    def test_base_substitute_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        c = logic.constant(0, 0)
        v = logic.variable(0, 0)
        with pytest.raises(NotImplementedError):
            s.substitute(c, v)

    def test_base_constants_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(NotImplementedError):
            s.constants()

    def test_base_variables_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(NotImplementedError):
            s.variables()

    def test_atomic_index_too_large(self):
        with pytest.raises(logic.Vocabulary.IndexTooLargeError):
            logic.atomic(logic.num_atomic_symbols, 0)
        
    def test_atomic_substitute(self):
        s = logic.atomic(0, 0)
        c = logic.constant(0, 0)
        v = logic.variable(0, 0)
        res = s.substitute(c, v)
        assert res == s

    def test_atomic_constants_empty(self):
        s = logic.atomic(0, 0)
        res = s.constants()
        assert len(res) == 0

    def test_atomic_variables_empty(self):
        s = logic.atomic(0, 0)
        res = s.variables()
        assert len(res) == 0

    def test_atomic_next_a0_to_b0(self):
        s = logic.atomic(0, 0)
        res = s.next()
        assert res.index == 1
        assert res.subscript == 0

    def test_atomic_next_e0_to_a1(self):
        s = logic.atomic(logic.num_atomic_symbols - 1, 0)
        res = s.next()
        assert res.index == 0
        assert res.subscript == 1

    def test_predicated_no_such_predicate_no_vocab(self):
        params = [logic.constant(0, 0), logic.constant(1, 0)]
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            logic.predicated('MyPredicate', params)

    def test_predicated_arity_mismatch_identity(self):
        params = [logic.constant(0, 0)]
        with pytest.raises(logic.Vocabulary.PredicateArityMismatchError):
            logic.predicated('Identity', params)

    def test_predicated_substitute_a_for_x_identity(self):
        s = logic.predicated('Identity', [logic.variable(0, 0), logic.constant(1, 0)])
        res = s.substitute(logic.constant(0, 0), logic.variable(0, 0))
        assert res.parameters[0] == logic.constant(0, 0)
        assert res.parameters[1] == logic.constant(1, 0)

    def test_quantified_substitute_inner_quantified(self):
        x = logic.variable(0, 0)
        y = logic.variable(1, 0)
        m = logic.constant(0, 0)
        s1 = logic.predicated('Identity', [x, y])
        s2 = logic.quantify('Existential', x, s1)
        s3 = logic.quantify('Existential', y, s2)
        res = s3.sentence.substitute(m, y)
        check = logic.parse('SxIxm')
        assert res == check

    def test_operated_no_such_operator(self):
        s = logic.atomic(0, 0)
        with pytest.raises(logic.Vocabulary.NoSuchOperatorError):
            logic.operate('Misjunction', [s, s])

    def test_operated_arity_mismatch_negation(self):
        s = logic.atomic(0, 0)
        with pytest.raises(logic.Vocabulary.OperatorArityMismatchError):
            logic.operate('Negation', [s, s])

    def test_constant_repr_contains_subscript(self):
        c = logic.constant(0, 8)
        res = str(c)
        assert '8' in res

    def test_base_sentence_not_implemented_various(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(NotImplementedError):
            s.atomics()
        with pytest.raises(NotImplementedError):
            s.predicates()
        with pytest.raises(NotImplementedError):
            s.hash_tuple()
        with pytest.raises(NotImplementedError):
            s.operators()

    def test_atomic_less_than_predicated(self):
        s1 = logic.atomic(0, 4)
        s2 = examples.predicated()
        assert s1 < s2
        assert s1 <= s2
        assert s2 > s1
        assert s2 >= s1

    def test_atomic_cmp_self_0_compat(self):
        s = logic.atomic(0, 0)
        assert s.__cmp__(s) == 0

    def test_sentence_operators_collection(self):
        s = logic.parse('KAMVxJxNbTNNImn')
        ops = s.operators()
        assert len(ops) == 7
        assert ','.join(ops) == 'Conjunction,Disjunction,Possibility,Negation,Assertion,Negation,Negation'

    def test_complex_quantified_substitution(self):
        vocab = logic.Vocabulary()
        vocab.declare_predicate('MyPred', 0, 0, 2)
        s1 = logic.parse('SxMVyFxy', vocabulary=vocab)
        m = logic.constant(0, 0)
        s2 = s1.sentence.substitute(m, s1.variable)
        s3 = logic.parse('MVyFmy', vocabulary=vocab)
        assert s2 == s3

    def test_with_pred_defs_single_pred_with_length4_name_raises_pred_err(self):
        with pytest.raises(logic.Vocabulary.PredicateError):
            logic.Vocabulary(('Pred', 0, 0, 1))

    def test_with_pred_defs_single_def_list(self):
        vocab = logic.Vocabulary([('Pred', 0, 0, 2)])
        predicate = vocab.get_predicate('Pred')
        assert predicate.arity == 2

    def test_with_pred_defs_single_def_tuple(self):
        vocab = logic.Vocabulary((('Pred', 0, 0, 3),))
        predicate = vocab.get_predicate('Pred')
        assert predicate.arity == 3

    def test_sorting_constants(self):
        c1 = logic.constant(1, 0)
        c2 = logic.constant(2, 0)
        res = list(sorted([c2, c1]))
        assert res[0] == c1
        assert res[1] == c2

    def test_sorting_predicated_sentences(self):
        c1 = logic.constant(1, 0)
        c2 = logic.constant(2, 0)
        vocab = logic.Vocabulary()
        p = vocab.declare_predicate('PredF', 0, 0, 1)
        s1 = logic.predicated(p, [c1])
        s2 = logic.predicated(p, [c2])
        sentences = [s2, s1]
        res = list(sorted(sentences))
        assert res[0] == s1
        assert res[1] == s2

class TestTableauxSystem(object):

    def test_build_trunk_base_not_impl(self):
        proof = logic.tableau(None, None)
        with pytest.raises(NotImplementedError):
            logic.TableauxSystem.build_trunk(proof, None)

def mock_sleep_5ms():
    time.sleep(0.005)

class TestTableau(object):

    def test_step_returns_false_when_finished(self):
        proof = logic.tableau(None, None)
        # force property
        proof.finished = True
        res = proof.step()
        assert not res

    def test_build_trunk_already_built_error(self):
        proof = logic.tableau('cpl', examples.argument('Addition'))
        with pytest.raises(logic.TableauxSystem.TrunkAlreadyBuiltError):
            proof.build_trunk()

    def test_repr_contains_finished(self):
        proof = logic.tableau('cpl', examples.argument('Addition'))
        res = proof.__repr__()
        assert 'finished' in res

    def test_build_premature_max_steps(self):
        proof = logic.tableau('cpl', examples.argument('Material Modus Ponens'))
        proof.build(max_steps=1)
        assert proof.is_premature

    def test_step_raises_trunk_not_built_with_hacked_arg_prop(self):
        proof = logic.tableau('cpl')
        proof.argument = examples.argument('Addition')
        with pytest.raises(logic.TableauxSystem.TrunkNotBuiltError):
            proof.step()

    def test_construct_sets_is_rank_optim_option(self):
        proof = logic.tableau('cpl', is_rank_optim=False)
        rule = proof.get_rule('Conjunction')
        assert not proof.opts['is_rank_optim']

    def test_timeout_1ms(self):
        proof = logic.tableau('cpl', examples.argument('Addition'))
        proof.step = mock_sleep_5ms
        with pytest.raises(logic.TableauxSystem.ProofTimeoutError):
            proof.build(build_timeout=1)

    def test_finish_empty_sets_build_duration_ms_0(self):
        proof = logic.tableau(None, None)
        proof.finish()
        assert proof.stats['build_duration_ms'] == 0

    def test_add_closure_rule_instance_mock(self):
        class MockRule(logic.TableauxSystem.ClosureRule):
            def applies_to_branch(self, branch):
                return True
            def check_for_target(self, node, branch):
                return True
            def node_will_close_branch(self, node, branch):
                return True
        proof = logic.tableau(None)
        rule = MockRule(proof)
        proof.add_closure_rule(rule).branch()
        proof.build()
        assert proof.valid

    def test_regress_structure_has_model_id(self):
        proof = logic.tableau('CPL', examples.argument('Triviality 1'))
        proof.build(is_build_models=True)
        assert proof.tree['model_id']

    #def test_add_rule_group_instance_mock(self):
    #    class MockRule1(logic.TableauxSystem.):

class TestBranch(object):

    def test_new_world_returns_w0(self):
        b = logic.TableauxSystem.Branch()
        res = b.new_world()
        assert res == 0

    def test_new_constant_returns_m(self):
        b = logic.TableauxSystem.Branch()
        res = b.new_constant()
        check = logic.constant(0, 0)
        assert res == check

    def test_new_constant_returns_m1_after_s0(self):
        b = logic.TableauxSystem.Branch()
        i = 0
        while i < logic.num_const_symbols:
            c = logic.constant(i, 0)
            sen = logic.predicated('Identity', [c, c])
            b.add({'sentence': sen})
            i += 1
        res = b.new_constant()
        check = logic.constant(0, 1)
        assert res == check

    def test_repr_contains_closed(self):
        b = logic.TableauxSystem.Branch()
        res = b.__repr__()
        assert 'closed' in res

    def test_has_all_true_1(self):
        b = logic.TableauxSystem.Branch()
        s1 = logic.atomic(0, 0)
        s2 = logic.atomic(1, 0)
        s3 = logic.atomic(2, 0)
        b.update([{'sentence': s1}, {'sentence': s2}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        assert b.has_all(check)

    def test_has_all_false_1(self):
        b = logic.TableauxSystem.Branch()
        s1 = logic.atomic(0, 0)
        s2 = logic.atomic(1, 0)
        s3 = logic.atomic(2, 0)
        b.update([{'sentence': s1}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        assert not b.has_all(check)

    def test_atomics_1(self):
        b = logic.TableauxSystem.Branch()
        s1 = logic.atomic(0, 0)
        s2 = logic.negate(logic.atomic(1, 0))
        s3 = logic.atomic(1, 0)
        b.update([{'sentence': s1}, {'sentence': s2}])
        res = b.atomics()
        assert s1 in res
        assert s3 in res

    def test_predicates(self):
        b = logic.TableauxSystem.Branch()
        s1 = examples.predicated()
        s2 = logic.negate(logic.negate(s1))
        b.add({'sentence': s2})
        assert s1.predicate in b.predicates()

    def test_make_model_raises_when_branch_closed(self):
        proof = logic.tableau('cpl', examples.argument('Addition'))
        proof.build()
        b = list(proof.branches)[0]
        with pytest.raises(logic.TableauxSystem.BranchClosedError):
            b.make_model()

    def test_branch_has_world1(self):
        proof = logic.tableau(None)
        branch = proof.branch().add({'world1': 4, 'world2': 1})
        assert branch.has({'world1': 4})

    def test_regression_branch_has_works_with_newly_added_node_on_register_node(self):

        class MyRule(logic.TableauxSystem.Rule):

            should_be = False
            shouldnt_be = True

            def register_node(self, node, branch):
                self.should_be = branch.has({'world1': 7})
                self.shouldnt_be = branch.has({'world1': 6})

        proof = logic.tableau(None)
        proof.add_rule_group([MyRule])
        rule = proof.get_rule(MyRule)
        proof.branch().add({'world1': 7})

        assert rule.should_be
        assert not rule.shouldnt_be

    def test_select_index_non_indexed_prop(self):
        branch = logic.TableauxSystem.Branch()
        branch.add({'foo': 'bar'})
        idx = branch._select_index({'foo': 'bar'}, None)
        assert idx == branch.nodes

    def test_close_adds_flag_node(self):
        branch = logic.TableauxSystem.Branch()
        branch.close()
        print(branch.nodes)
        assert branch.has({'is_flag': True, 'flag': 'closure'})

    def test_constants_or_new_returns_pair_no_constants(self):
        branch = logic.TableauxSystem.Branch()
        res = branch.constants_or_new()
        assert len(res) == 2
        constants, is_new = res
        assert len(constants) == 1
        assert is_new

    def test_constants_or_new_returns_pair_with_constants(self):
        branch = logic.TableauxSystem.Branch()
        branch.add({'sentence': logic.parse('Imn')})
        res = branch.constants_or_new()
        assert len(res) == 2
        constants, is_new = res
        assert len(constants) == 2
        assert not is_new

class TestNode(object):

    def test_worlds_contains_worlds(self):
        node = logic.TableauxSystem.Node({'worlds': set([0, 1])})
        res = node.worlds()
        assert 0 in res
        assert 1 in res

    def test_repr_contains_prop_key(self):
        node = logic.TableauxSystem.Node({'foo': 1})
        res = node.__repr__()
        assert 'foo' in res

    def test_clousre_flag_node_has_is_flag(self):
        branch = logic.TableauxSystem.Branch()
        branch.close()
        node = branch.nodes[0]
        assert node.has('is_flag')

class TestRule(object):

    def test_base_not_impl_various(self):
        rule = logic.TableauxSystem.Rule(logic.tableau(None, None))
        with pytest.raises(NotImplementedError):
            rule.get_candidate_targets(None)

    def test_base_repr_equals_rule(self):
        rule = logic.TableauxSystem.Rule(logic.tableau(None, None))
        res = rule.__repr__()
        assert res == 'Rule'

class TestClosureRule(object):

    def test_applies_to_branch_not_impl(self):
        rule = logic.TableauxSystem.ClosureRule(logic.tableau(None, None))
        with pytest.raises(NotImplementedError):
            rule.applies_to_branch(None)

class TestNodeRule(object):

    def test_not_impl_various(self):
        rule = logic.TableauxSystem.PotentialNodeRule(logic.tableau(None, None))
        with pytest.raises(NotImplementedError):
            rule.apply_to_node(None, None)
        with pytest.raises(NotImplementedError):
            rule.example_node(None)
        with pytest.raises(NotImplementedError):
            rule.example()

class TestFilterNodeRule(object):

    def proof_with_rule(self, Rule):
        proof = logic.tableau(None).add_rule_group([Rule])
        return (proof, proof.get_rule(Rule))
        
    def test_applies_to_empty_nodes_when_no_properties_defined(self):

        class MockFilterRule(logic.TableauxSystem.FilterNodeRule):
            pass

        proof, rule = self.proof_with_rule(MockFilterRule)
        node = logic.TableauxSystem.Node()
        branch = proof.branch().add(node)
        assert rule.get_target_for_node(node, branch)

    def test_default_does_not_apply_to_ticked_node(self):

        class MockFilterRule(logic.TableauxSystem.FilterNodeRule):
            pass

        proof, rule = self.proof_with_rule(MockFilterRule)
        node = logic.TableauxSystem.Node()
        branch = proof.branch().add(node)
        branch.tick(node)
        assert not rule.get_target_for_node(node, branch)

    def test_applies_to_ticked_node_with_prop_none(self):

        class MockFilterRule(logic.TableauxSystem.FilterNodeRule):
            ticked = None

        proof, rule = self.proof_with_rule(MockFilterRule)
        node = logic.TableauxSystem.Node()
        branch = proof.branch().add(node)
        branch.tick(node)
        assert rule.get_target_for_node(node, branch)
        
class TestModel(object):

    def test_not_impl_various(self):
        model = logic.Model()
        with pytest.raises(NotImplementedError):
            model.read_branch(None)
        with pytest.raises(NotImplementedError):
            model.truth_function(None, None)
        with pytest.raises(NotImplementedError):
            model.value_of_opaque(None)
        with pytest.raises(NotImplementedError):
            model.value_of_predicated(None)
        with pytest.raises(NotImplementedError):
            s = logic.negate(logic.atomic(0, 0))
            model.value_of_operated(s)
        with pytest.raises(NotImplementedError):
            model.value_of_quantified(None)
        with pytest.raises(NotImplementedError):
            model.is_countermodel_to(None)
        with pytest.raises(NotImplementedError):
            model.value_of_atomic(None)

    def test_get_data_empty(self):
        model = logic.Model()
        res = model.get_data()
        assert len(res) == 0