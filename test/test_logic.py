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
        with pytest.raises(logic.NotImplementedError):
            s.substitute(c, v)

    def test_base_constants_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(logic.NotImplementedError):
            s.constants()

    def test_base_variables_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(logic.NotImplementedError):
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
        res = s3.substitute(m, y)
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
        with pytest.raises(logic.NotImplementedError):
            s.atomics()
        with pytest.raises(logic.NotImplementedError):
            s.predicates()
        with pytest.raises(logic.NotImplementedError):
            s.hash_tuple()
        with pytest.raises(logic.NotImplementedError):
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

class TestTableauxSystem(object):

    def test_build_trunk_base_not_impl(self):
        proof = logic.tableau(None, None)
        with pytest.raises(logic.NotImplementedError):
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
        assert not rule.is_rank_optim

    def test_timeout_1ms(self):
        proof = logic.tableau('cpl', examples.argument('Addition'))
        proof.step = mock_sleep_5ms
        with pytest.raises(logic.TableauxSystem.ProofTimeoutError):
            proof.build(timeout=1)

    def test_finish_empty_sets_build_duration_ms_none(self):
        proof = logic.tableau(None, None)
        proof.finish()
        assert proof.stats['build_duration_ms'] == None

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

class TestRule(object):

    def test_base_applies_not_impl(self):
        rule = logic.TableauxSystem.Rule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.applies()

    def test_base_apply_not_impl(self):
        rule = logic.TableauxSystem.Rule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.apply(None)

    def test_base_example_not_impl(self):
        rule = logic.TableauxSystem.Rule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.example()

    def test_base_repr_equals_rule(self):
        rule = logic.TableauxSystem.Rule(logic.tableau(None, None))
        res = rule.__repr__()
        assert res == 'Rule'

class TestBranchRule(object):

    def test_applies_to_branch_not_impl(self):
        rule = logic.TableauxSystem.BranchRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.applies_to_branch(None)

    def test_target_has_branch_when_returns_true_mock(self):
        class MockRule(logic.TableauxSystem.BranchRule):
            def applies_to_branch(self, branch):
                return True
        proof = logic.tableau(None, None)
        branch = proof.branch()
        rule = MockRule(proof)
        res = rule.applies()
        assert res['branch'] == branch

class TestClosureRule(object):

    def test_applies_to_branch_not_impl(self):
        rule = logic.TableauxSystem.ClosureRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.applies_to_branch(None)

class TestNodeRule(object):

    def test_applies_to_node_not_impl(self):
        rule = logic.TableauxSystem.NodeRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.applies_to_node(None, None)

    def test_apply_to_node_not_impl(self):
        rule = logic.TableauxSystem.NodeRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.apply_to_node(None, None)

    def test_example_node_not_impl(self):
        rule = logic.TableauxSystem.NodeRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.example_node()

    def test_example_not_impl(self):
        rule = logic.TableauxSystem.NodeRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.example()

class TestSelectiveTrackingBranchRule(object):

    def test_not_impl_various(self):
        rule = logic.TableauxSystem.SelectiveTrackingBranchRule(logic.tableau(None, None))
        with pytest.raises(logic.NotImplementedError):
            rule.get_candidate_targets_for_branch(None)
        with pytest.raises(logic.NotImplementedError):
            rule.apply_to_target(None)

class TestModel(object):

    def test_not_impl_various(self):
        model = logic.Model()
        with pytest.raises(logic.NotImplementedError):
            model.read_branch(None)
        with pytest.raises(logic.NotImplementedError):
            model.truth_function(None, None)
        with pytest.raises(logic.NotImplementedError):
            model.value_of_opaque(None)
        with pytest.raises(logic.NotImplementedError):
            model.value_of_predicated(None)
        with pytest.raises(logic.NotImplementedError):
            s = logic.negate(logic.atomic(0, 0))
            model.value_of_operated(s)
        with pytest.raises(logic.NotImplementedError):
            model.value_of_quantified(None)
        with pytest.raises(logic.NotImplementedError):
            model.is_countermodel_to(None)
        with pytest.raises(logic.NotImplementedError):
            model.value_of_atomic(None)

    def test_get_data_empty(self):
        model = logic.Model()
        res = model.get_data()
        assert len(res) == 0