
from errors import *
from events import Events
from proof.tableaux import TableauxSystem as TabSys, Branch, Node, Tableau
from proof.rules import FilterNodeRule, ClosureRule, PotentialNodeRule, Rule
from proof.helpers import NodeFilter
from lexicals import Atomic, Constant, Predicated
from utils import get_logic
import examples

import time
from pytest import raises
from .testutils import LogicTester

class TestTableauxSystem(object):

    def test_build_trunk_base_not_impl(self):
        proof = Tableau(None, None)
        with raises(NotImplementedError):
            TabSys.build_trunk(proof, None)

def mock_sleep_5ms():
    time.sleep(0.005)

def exarg(*args, **kw):
    return examples.argument(*args, **kw)

class TestTableau(object):

    def test_step_returns_false_when_finished(self):
        res = Tableau(None).finish().step()
        assert res == False

    def test_build_trunk_already_built_error(self):
        proof = Tableau('cpl', exarg('Addition'))
        with raises(IllegalStateError):
            proof.build_trunk()

    def test_repr_contains_finished(self):
        proof = Tableau('cpl', exarg('Addition'))
        res = proof.__repr__()
        assert 'finished' in res

    def test_build_premature_max_steps(self):
        proof = Tableau('cpl', exarg('Material Modus Ponens'), max_steps=1)
        proof.build()
        assert proof.premature

    def test_construct_sets_is_rank_optim_option(self):
        proof = Tableau('cpl', is_rank_optim=False)
        rule = proof.get_rule('Conjunction')
        assert not proof.opts['is_rank_optim']

    def test_timeout_1ms(self):
        proof = Tableau('cpl', exarg('Addition'), build_timeout=1)
        proof.step = mock_sleep_5ms
        with raises(TimeoutError):
            proof.build()

    def test_finish_empty_sets_build_duration_ms_0(self):
        proof = Tableau(None)
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
        proof.add_closure_rule(MockRule).branch()
        assert proof.open_branch_count == 1
        proof.build()
        assert proof.open_branch_count == 0

    def test_regress_structure_has_model_id(self):
        proof = Tableau('CPL', exarg('Triviality 1'), is_build_models=True)
        proof.build()
        assert proof.tree['model_id']

    def test_getrule_returns_arg_if_rule_instance(self):
        proof = Tableau('CPL')
        rule = proof.get_rule('Conjunction')
        assert isinstance(rule, Rule)
        r = proof.get_rule(rule)
        assert isinstance(r, Rule)
        assert r is rule

    def test_after_branch_add_with_nodes_no_parent(self):

        class MockRule(Rule):
            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                self.tableau.add_listener(Events.AFTER_BRANCH_ADD, self.__after_branch_add)

            def __after_branch_add(self, branch):
                self._checkbranch = branch
                self._checkparent = branch.parent
        b = Branch().add({'test': True})
        proof = Tableau(None).add_rule_group([MockRule]).add_branch(b)
        # proof
        
        # proof.add_branch(b)
        rule = proof.get_rule(MockRule)
        assert rule._checkbranch is b
        assert rule._checkparent == None
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
        while i <= Constant.MAXI:
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

    def test_branch_has_world1(self):
        proof = Tableau(None)
        branch = proof.branch().add({'world1': 4, 'world2': 1})
        assert branch.has({'world1': 4})

    def test_regression_branch_has_works_with_newly_added_node_on_after_node_add(self):

        class MyRule(Rule):

            should_be = False
            shouldnt_be = True

            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                self.tableau.add_listener(Events.AFTER_NODE_ADD, self.__after_node_add)

            def __after_node_add(self, node, branch):
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
            rule._get_targets(None)

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
            rule.apply_to_node_target(None, None, None)

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


class Test_NodeFilter_CPL(LogicTester):

    logic = get_logic('CPL')

    def test_node_method_filter_has_props_sentence(self):

        s1, s2 = self.pp('a', 'b')
        n1, n2 = (Node({'sentence': s}) for s in (s1, s2))

        nfilter = NodeFilter.node_method_filter(
            'has_props', {'sentence': s1}
        )
        assert nfilter(n1)
        assert not nfilter(n2)

    def test_node_filter_on_tableau(self):
        s1, s2 = self.pp('a', 'b')
        nfilter = NodeFilter.node_method_filter(
            'has_props', {'sentence': s1}
        )
        class TestRuleImpl(Rule):
            Helpers = (('nf', NodeFilter),)
        
        tab = self.tab()
        tab.clear_rules()
        rule = tab.add_rule_group([TestRuleImpl]).get_rule(TestRuleImpl)
        nf = rule.nf
        nf.add_filter(nfilter)
        b = tab.branch().update((
            {'sentence': s1},
            {'sentence': s2},
        ))
        nodes = list(nf.get_nodes(b))
        assert len(nodes) == 1