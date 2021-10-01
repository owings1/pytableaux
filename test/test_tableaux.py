
from errors import *

from tableaux import TableauxSystem as TabSys, Branch, Node, Tableau, \
    FilterNodeRule, ClosureRule, PotentialNodeRule, Rule
from lexicals import Atomic, Constant, Predicated
import examples

from fixed import num_const_symbols
import time
from pytest import raises

class TestTableauxSystem(object):

    def test_build_trunk_base_not_impl(self):
        proof = Tableau(None, None)
        with raises(NotImplementedError):
            TabSys.build_trunk(proof, None)

def mock_sleep_5ms():
    time.sleep(0.005)

class TestTableau(object):

    def test_step_returns_false_when_finished(self):
        proof = Tableau(None, None)
        # force property
        proof.finished = True
        res = proof.step()
        assert not res

    def test_build_trunk_already_built_error(self):
        proof = Tableau('cpl', examples.argument('Addition'))
        with raises(TrunkAlreadyBuiltError):
            proof.build_trunk()

    def test_repr_contains_finished(self):
        proof = Tableau('cpl', examples.argument('Addition'))
        res = proof.__repr__()
        assert 'finished' in res

    def test_build_premature_max_steps(self):
        proof = Tableau('cpl', examples.argument('Material Modus Ponens'))
        proof.build(max_steps=1)
        assert proof.is_premature

    def test_step_raises_trunk_not_built_with_hacked_arg_prop(self):
        proof = Tableau('cpl')
        proof.argument = examples.argument('Addition')
        with raises(TrunkNotBuiltError):
            proof.step()

    def test_construct_sets_is_rank_optim_option(self):
        proof = Tableau('cpl', is_rank_optim=False)
        rule = proof.get_rule('Conjunction')
        assert not proof.opts['is_rank_optim']

    def test_timeout_1ms(self):
        proof = Tableau('cpl', examples.argument('Addition'))
        proof.step = mock_sleep_5ms
        with raises(ProofTimeoutError):
            proof.build(build_timeout=1)

    def test_finish_empty_sets_build_duration_ms_0(self):
        proof = Tableau(None, None)
        proof.finish()
        assert proof.stats['build_duration_ms'] == 0

    def test_add_closure_rule_instance_mock(self):
        class MockRule(ClosureRule):
            def applies_to_branch(self, branch):
                return True
            def check_for_target(self, node, branch):
                return True
            def node_will_close_branch(self, node, branch):
                return True
        proof = Tableau(None)
        rule = MockRule(proof)
        proof.add_closure_rule(rule).branch()
        proof.build()
        assert proof.valid

    def test_regress_structure_has_model_id(self):
        proof = Tableau('CPL', examples.argument('Triviality 1'))
        proof.build(is_build_models=True)
        assert proof.tree['model_id']

    #def test_add_rule_group_instance_mock(self):
    #    class MockRule1():

class TestBranch(object):

    def test_new_world_returns_w0(self):
        b = Branch()
        res = b.new_world()
        assert res == 0

    def test_new_constant_returns_m(self):
        b = Branch()
        res = b.new_constant()
        check = Constant(0, 0)
        assert res == check

    def test_new_constant_returns_m1_after_s0(self):
        b = Branch()
        i = 0
        while i < num_const_symbols:
            c = Constant(i, 0)
            sen = Predicated('Identity', [c, c])
            b.add({'sentence': sen})
            i += 1
        res = b.new_constant()
        check = Constant(0, 1)
        assert res == check

    def test_repr_contains_closed(self):
        b = Branch()
        res = b.__repr__()
        assert 'closed' in res

    def test_has_all_true_1(self):
        b = Branch()
        s1 = Atomic(0, 0)
        s2 = Atomic(1, 0)
        s3 = Atomic(2, 0)
        b.update([{'sentence': s1}, {'sentence': s2}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        assert b.has_all(check)

    def test_has_all_false_1(self):
        b = Branch()
        s1 = Atomic(0, 0)
        s2 = Atomic(1, 0)
        s3 = Atomic(2, 0)
        b.update([{'sentence': s1}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        assert not b.has_all(check)

    def test_atomics_1(self):
        b = Branch()
        s1 = Atomic(0, 0)
        s2 = Atomic(1, 0).negate()
        s3 = Atomic(1, 0)
        b.update([{'sentence': s1}, {'sentence': s2}])
        res = b.atomics()
        assert s1 in res
        assert s3 in res

    def test_predicates(self):
        b = Branch()
        s1 = examples.predicated()
        s2 = s1.negate().negate()
        b.add({'sentence': s2})
        assert s1.predicate in b.predicates()

    def test_make_model_raises_when_branch_closed(self):
        proof = Tableau('cpl', examples.argument('Addition'))
        proof.build()
        b = list(proof.branches)[0]
        with raises(BranchClosedError):
            b.make_model()

    def test_branch_has_world1(self):
        proof = Tableau(None)
        branch = proof.branch().add({'world1': 4, 'world2': 1})
        assert branch.has({'world1': 4})

    def test_regression_branch_has_works_with_newly_added_node_on_register_node(self):

        class MyRule(Rule):

            should_be = False
            shouldnt_be = True

            def register_node(self, node, branch):
                self.should_be = branch.has({'world1': 7})
                self.shouldnt_be = branch.has({'world1': 6})

        proof = Tableau(None)
        proof.add_rule_group([MyRule])
        rule = proof.get_rule(MyRule)
        proof.branch().add({'world1': 7})

        assert rule.should_be
        assert not rule.shouldnt_be

    def test_select_index_non_indexed_prop(self):
        branch = Branch()
        branch.add({'foo': 'bar'})
        idx = branch._select_index({'foo': 'bar'}, None)
        assert idx == branch.nodes

    def test_close_adds_flag_node(self):
        branch = Branch()
        branch.close()
        print(branch.nodes)
        assert branch.has({'is_flag': True, 'flag': 'closure'})

    def test_constants_or_new_returns_pair_no_constants(self):
        branch = Branch()
        res = branch.constants_or_new()
        assert len(res) == 2
        constants, is_new = res
        assert len(constants) == 1
        assert is_new

    def test_constants_or_new_returns_pair_with_constants(self):
        branch = Branch()
        s1 = Predicated('Identity', [Constant(0, 0), Constant(1, 0)])
        branch.add({'sentence': s1})
        res = branch.constants_or_new()
        assert len(res) == 2
        constants, is_new = res
        assert len(constants) == 2
        assert not is_new

class TestNode(object):

    def test_worlds_contains_worlds(self):
        node = Node({'worlds': set([0, 1])})
        res = node.worlds()
        assert 0 in res
        assert 1 in res

    def test_repr_contains_prop_key(self):
        node = Node({'foo': 1})
        res = node.__repr__()
        assert 'foo' in res

    def test_clousre_flag_node_has_is_flag(self):
        branch = Branch()
        branch.close()
        node = branch.nodes[0]
        assert node.has('is_flag')

class TestRule(object):

    def test_base_not_impl_various(self):
        rule = Rule(Tableau(None, None))
        with raises(NotImplementedError):
            rule.get_candidate_targets(None)

    def test_base_repr_equals_rule(self):
        rule = Rule(Tableau(None, None))
        res = rule.__repr__()
        assert res == 'Rule'

class TestClosureRule(object):

    def test_applies_to_branch_not_impl(self):
        rule = ClosureRule(Tableau(None, None))
        with raises(NotImplementedError):
            rule.applies_to_branch(None)

class TestNodeRule(object):

    def test_not_impl_various(self):
        rule = PotentialNodeRule(Tableau(None, None))
        with raises(NotImplementedError):
            rule.apply_to_node(None, None)
        with raises(NotImplementedError):
            rule.example_node(None)
        with raises(NotImplementedError):
            rule.example()

class TestFilterNodeRule(object):

    def proof_with_rule(self, Rule):
        proof = Tableau(None).add_rule_group([Rule])
        return (proof, proof.get_rule(Rule))
        
    def test_applies_to_empty_nodes_when_no_properties_defined(self):

        class MockFilterRule(FilterNodeRule):
            pass

        proof, rule = self.proof_with_rule(MockFilterRule)
        node = Node()
        branch = proof.branch().add(node)
        assert rule.get_target_for_node(node, branch)

    def test_default_does_not_apply_to_ticked_node(self):

        class MockFilterRule(FilterNodeRule):
            pass

        proof, rule = self.proof_with_rule(MockFilterRule)
        node = Node()
        branch = proof.branch().add(node)
        branch.tick(node)
        assert not rule.get_target_for_node(node, branch)

    def test_applies_to_ticked_node_with_prop_none(self):

        class MockFilterRule(FilterNodeRule):
            ticked = None

        proof, rule = self.proof_with_rule(MockFilterRule)
        node = Node()
        branch = proof.branch().add(node)
        branch.tick(node)
        assert rule.get_target_for_node(node, branch)