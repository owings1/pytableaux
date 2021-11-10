
from errors import *
from events import Events
from proof.tableaux import TableauxSystem as TabSys, Branch, Node, Tableau
from proof.rules import FilterNodeRule, ClosureRule, PotentialNodeRule, Rule
from proof.helpers import AdzHelper, FilterHelper
from proof.common import Getters, Filters
from lexicals import Atomic, Constant, Predicated
from utils import get_logic
import examples

import time
from pytest import raises
from .tutils import BaseSuite,  using

class TestTableauxSystem(object):

    def test_build_trunk_base_not_impl(self):
        proof = Tableau()
        with raises(NotImplementedError):
            TabSys.build_trunk(proof, None)

def mock_sleep_5ms():
    time.sleep(0.005)

def exarg(*args, **kw):
    return examples.argument(*args, **kw)

@using(logic = 'CPL')
class TestTableau(BaseSuite):

    def test_step_returns_false_when_finished(self):
        assert Tableau().finish().step() == False

    def test_build_trunk_already_built_error(self):
        tab = self.tab('Addition')
        with raises(IllegalStateError):
            tab.build_trunk()

    def test_repr_contains_finished(self):
        tab = self.tab('Addition')
        assert 'finished' in tab.__repr__()

    def test_build_premature_max_steps(self):
        tab = self.tab('Material Modus Ponens', max_steps=1)
        assert tab.premature

    def test_construct_sets_is_rank_optim_option(self):
        proof = Tableau('cpl', is_rank_optim=False)
        assert proof.rules.get('Conjunction')
        assert not proof.opts['is_rank_optim']

    def test_timeout_1ms(self):
        proof = Tableau('cpl', exarg('Addition'), build_timeout=1)
        proof.step = mock_sleep_5ms
        with raises(TimeoutError):
            proof.build()

    def test_finish_empty_sets_build_duration_ms_0(self):
        proof = Tableau().finish()
        assert proof.stats['build_duration_ms'] == 0

    def test_add_closure_rule_instance_mock(self):
        class MockRule(ClosureRule):
            def applies_to_branch(self, branch):
                return True
            def check_for_target(self, node, branch):
                return True
            def node_will_close_branch(self, node, branch):
                return True
        tab = Tableau()
        tab.rules.add(MockRule)
        tab.branch()
        assert len(tab.open) == 1
        tab.build()
        assert len(tab.open) == 0

    def test_regress_structure_has_model_id(self):
        proof = Tableau('CPL', exarg('Triviality 1'), is_build_models=True)
        proof.build()
        assert proof.tree['model_id']

    def test_getrule_returns_arg_if_rule_instance(self):
        proof = Tableau('CPL')
        rule = proof.rules.get('Conjunction')
        assert isinstance(rule, Rule)
        r = proof.rules.get(rule)
        assert isinstance(r, Rule)
        assert r is rule

# from proof.tableaux import *
# import examples
# arg = examples.argument('Triviality 1')
# tab = Tableau('cpl', arg)
    def test_after_branch_add_with_nodes_no_parent(self):

        class MockRule(Rule):
            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                self.tableau.on(Events.AFTER_BRANCH_ADD, self.__after_branch_add)

            def __after_branch_add(self, branch):
                self._checkbranch = branch
                self._checkparent = branch.parent
        b = Branch().add({'test': True})
        tab = Tableau()
        tab.rules.add(MockRule)
        tab.add(b)
        # proof
        
        # proof.add(b)
        rule = tab.rules.get(MockRule)
        assert rule._checkbranch is b
        assert rule._checkparent == None
    #def test_add_rule_group_instance_mock(self):
    #    class MockRule1():

class TestBranch(object):

    def test_next_world_returns_w0(self):
        assert Branch().next_world == 0

    def test_new_constant_returns_m(self):
        assert Branch().new_constant() == Constant(0, 0)

    def test_new_constant_returns_m1_after_s0(self):
        b = Branch()
        i = 0
        while i <= Constant.TYPE.maxi:
            c = Constant(i, 0)
            sen = Predicated('Identity', [c, c])
            b.add({'sentence': sen})
            i += 1
        res = b.new_constant()
        check = Constant(0, 1)
        assert res == check

    def test_repr_contains_closed(self):
        assert 'closed' in Branch().__repr__()

    def test_has_all_true_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{'sentence': s1}, {'sentence': s2}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        assert b.has_all(check)

    def test_has_all_false_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{'sentence': s1}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        assert not b.has_all(check)

    # def test_atomics_1(self):
    #     b = Branch()
    #     s1 = Atomic(0, 0)
    #     s2 = Atomic(1, 0).negate()
    #     s3 = Atomic(1, 0)
    #     b.extend([{'sentence': s1}, {'sentence': s2}])
    #     res = b.atomics
    #     assert s1 in res
    #     assert s3 in res

    # def test_predicates(self):
    #     b = Branch()
    #     s1 = examples.predicated()
    #     s2 = s1.negate().negate()
    #     b.add({'sentence': s2})
    #     assert s1.predicate in b.predicates()

    def test_branch_has_world1(self):
        proof = Tableau()
        branch = proof.branch().add({'world1': 4, 'world2': 1})
        assert branch.has({'world1': 4})

    def test_regression_branch_has_works_with_newly_added_node_on_after_node_add(self):

        class MyRule(Rule):

            should_be = False
            shouldnt_be = True

            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                self.tableau.on(Events.AFTER_NODE_ADD, self.__after_node_add)

            def __after_node_add(self, node, branch):
                self.should_be = branch.has({'world1': 7})
                self.shouldnt_be = branch.has({'world1': 6})

        proof = Tableau()
        proof.rules.add(MyRule)
        rule = proof.rules.MyRule
        proof.branch().add({'world1': 7})

        assert rule.should_be
        assert not rule.shouldnt_be

    def test_has_access_1(self):
        b = Branch().extend((
            {'world1': 0, 'world2': 1},
            {'world1': 4, 'world2': 3},
            {'world1': 4, 'world2': 4},
        ))
        with raises(TypeError):
            b.has_access(0, 1, 4)
        assert b.has_access(0, 1)
        assert b.has_access(4, 3)
        assert b.has_access(4, 4)
        assert not b.has_access(3, 3)

    def test_select_index_non_indexed_prop(self):
        branch = Branch()
        branch.add({'foo': 'bar'})
        idx = branch._Branch__select_index({'foo': 'bar'}, None)
        assert list(idx) == list(branch)

    def test_select_index_access(self):
        b = Branch().extend((
            {'world1': 0, 'world2': 1},
            {'foo': 'bar'},
        ))
        idx = b._Branch__select_index({'world1': 0, 'world2': 1}, None)
        assert set(idx) == {b[0]}

    def test_close_adds_flag_node(self):
        branch = Branch()
        branch.close()
        assert branch.has({'is_flag': True, 'flag': 'closure'})

    # def test_constants_or_new_returns_pair_no_constants(self):
    #     branch = Branch()
    #     res = branch.constants_or_new()
    #     assert len(res) == 2
    #     constants, is_new = res
    #     assert len(constants) == 1
    #     assert is_new

    # def test_constants_or_new_returns_pair_with_constants(self):
    #     branch = Branch()
    #     s1 = Predicated('Identity', [Constant(0, 0), Constant(1, 0)])
    #     branch.add({'sentence': s1})
    #     res = branch.constants_or_new()
    #     assert len(res) == 2
    #     constants, is_new = res
    #     assert len(constants) == 2
    #     assert not is_new

    def nn1(self, n = 3):
        return tuple(Node({'i': i}) for i in range(n))

    def case1(self, n = 3, nn = None):
        b = Branch()
        if not any ((n, nn)):
            return b
        if nn == None:
            nn = self.nn1(n)
        b.extend(nn)
        return (b, nn)

    def test_for_in_iter_nodes(self):
        b, nn = self.case1()
        assert tuple(n for n in iter(b)) == nn
        assert tuple(n for n in b) == nn

    def test_subscript_1(self):
        b, nn = self.case1(n=5)
        assert b[0] == nn[0]
        assert b[-1] == nn[4]
        assert b[0:1] == list(nn)[0:1]
        assert b[2:-1] == [nn[2], nn[3]]
        assert b[3:] == [nn[3], nn[4]]

    def test_create_list_tuple_set_from_branch(self):
        b, nn = self.case1(5)
        nodes = list(b)
        assert tuple(b) == nn
        assert set(b) == set(nn)
        assert nodes == list(nn)
        assert len(nodes) == len(b)
        assert len(nodes) == 5

    def case2(self, n = 2):
        return Branch().extend(self.nn1(n=n))

    def test_subscript_type_error_non_num(self):
        b = self.case2()
        with raises(TypeError):
            b['0']

    def test_subscript_index_error_1(self):
        b = self.case2(2)
        with raises(IndexError):
            b[2]

    def test_len_0_6(self):
        assert len(self.case2(0)) == 0
        assert len(self.case2(6)) == 6


class TestNode(object):

    def test_worlds_contains_worlds(self):
        node = Node({'worlds': set([0, 1])})
        res = node.worlds
        assert 0 in res
        assert 1 in res

    def test_clousre_flag_node_has_is_flag(self):
        branch = Branch()
        branch.close()
        node = branch[0]
        assert node.has('is_flag')

class TestRule(object):

    def test_base_not_impl_various(self):
        rule = Rule(Tableau())
        with raises(NotImplementedError):
            rule._get_targets(None)

    def test_base_repr_equals_rule(self):
        rule = Rule(Tableau())
        res = rule.__repr__()
        assert 'Rule' in res

class TestClosureRule(object):

    def test_applies_to_branch_not_impl(self):
        rule = ClosureRule(Tableau())
        with raises(NotImplementedError):
            rule.applies_to_branch(None)

class TestNodeRule(object):

    def test_not_impl_various(self):
        rule = PotentialNodeRule(Tableau())
        with raises(NotImplementedError):
            rule.apply_to_node_target(None, None, None)

class TestFilterNodeRule(object):

    def proof_with_rule(self, Rule):
        proof = Tableau()
        proof.rules.add(Rule)
        return (proof, proof.rules.get(Rule))
        
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

class TestFilters(BaseSuite):

    def test_MethodFilter_node_has_props_sentence(self):
        s1, s2 = self.pp('a', 'b')
        f = Filters.Method('has_props', {'sentence': s1})
        assert f(Node({'sentence': s1}))
        assert not f(Node({'sentence': s2}))

    def test_AttrFilter_node_is_modal(self):
        class Lhs(object):
            testname = True
        f = Filters.Attr(Lhs(), testname = 'is_modal')
        assert f(Node({'world1': 0}))
        assert not f(Node({'foo': 'bar'}))

    def test_AttrFilter_key_node_designated(self):
        class Lhs(object):
            testname = True
        f = Filters.Attr(Lhs(), testname = 'designated')
        f.rget = Getters.Key()
        assert f(Node({'designated': True}))
        assert not f(Node({'foo': 'bar'}))

class NodeFilterRule(Rule):

    ignore_ticked = None
    designation = None
    modal = None
    negated = operator = quantifier = predicate = None

    Helpers = (
        ('nf', FilterHelper),
        ('adz', AdzHelper),
    )

    class DesignationFilter(Filters.Attr):
        attrs = (('designation', 'designated'),)
        rget = Getters.key

    class ModalFilter(Filters.Attr):
        attrs = (('modal', 'is_modal'),)

    NodeFilters = (
        ('designation', DesignationFilter),
        ('modal', ModalFilter),
        ('sentence', Filters.Node.Sentence),
    )

@using(logic = 'CPL')
class Test_NodeFilter(BaseSuite):

    def nn1(self, n = 2):
        return tuple(
            Node({
                'sentence': s,
                'designated': None if i == 0 else bool(i % 2),
            })
            for i, s in enumerate(self.sgen(n))
        )

    def case1(self, cls, n = 2, nn = None):
        rule, tab = self.rule_tab(cls)
        nf = rule.nf
        b = tab.branch()
        if not any ((n, nn)):
            return (nf, b)
        if nn == None:
            nn = self.nn1(n)
        b.extend(nn)
        return (nf, b, nn)

    def test_filters_view(self):
        nf, b, nn = self.case1(NodeFilterRule, 4)
        fview = nf.filters
        assert len(fview) == 3
        assert 'sentence' in fview
        assert isinstance(fview.sentence, Filters.Node.Sentence)
        assert fview['sentence'] == fview.sentence
        assert fview.sentence in set(fview)
        with raises(AttributeError):
            fview.foo
        with raises(AttributeError):
            del(fview.sentence)
        with raises(TypeError):
            del(fview['sentence'])

    def test_sentence_no_filters(self):
        nf, b, nn = self.case1(NodeFilterRule)
        lhs = nf.rule
        assert not any((lhs.operator, lhs.quantifier, lhs.predicate))
        sf = nf.filters[-1]
        assert sf._Sentence__applies == False
        assert nf[b] == set(nn)
        assert nf[b] == set(b)

    def test_sentence_operator(self):
        class Impl(NodeFilterRule):
            operator = 'Conjunction'
        nf, b, nn = self.case1(Impl)
        assert nf[b] == {nn[0]}

    def test_exclude_ticked_default(self):
        nf, b, nn = self.case1(NodeFilterRule)
        b.tick(nn[0])
        assert nf[b] == {nn[1]}

    def test_ignore_ticked_helper_attr(self):
        nf, b, nn = self.case1(NodeFilterRule, n=3)
        nf.ignore_ticked = True
        b.tick(nn[0], nn[1])
        assert nf[b] == set(nn)

    def test_ignore_ticked_rule_cls_attr(self):
        class Impl(NodeFilterRule):
            ignore_ticked = True
        nf, b, nn = self.case1(Impl, n=3)
        b.tick(nn[0], nn[1])
        assert nf[b] == set(nn)

    def test_ignore_ticked_rule_attr_pre_super(self):
        class Impl(NodeFilterRule):
            def __init__(self, *args, **opts):
                self.ignore_ticked = True
                super().__init__(*args, **opts)
        nf, b, nn = self.case1(Impl, n=3)
        b.tick(nn[0], nn[1])
        assert nf[b] == set(nn)

    def test_ignore_ticked_rule_attr_post_init(self):
        class Impl(NodeFilterRule):
            ignore_ticked = False
        nf, b = self.case1(Impl, n = None)
        nn = self.nn1(3)
        assert nf.ignore_ticked == False
        nf.rule.ignore_ticked = True
        b.extend(nn).tick(nn[0], nn[1])
        assert nf[b] == set(nn)

    def test_designation_true(self):
        class Impl(NodeFilterRule):
            designation = True
        nf, b, nn = self.case1(Impl, n=3)
        assert nf[b] == {nn[1]}

DefaultKRule = get_logic('K').DefaultNodeRule
@using(logic = 'K')
class Test_K_DefaultNodeFilterRule(BaseSuite):

    def ngen(self, n):
        sgen = self.sgen(n)
        wn = 0
        for i in range(n):
            s = sgen.__next__()
            if i == 0:
                n = {'sentence':s}
            elif i % 3 == 0:
                w1 = wn
                w2 = wn = w1 + 1
                n = {'world1':w1, 'world2':w2}
            else:
                n = {'sentence':s, 'world':wn}
            yield Node(n)
        sgen.close()

    def case1(self, n = 10, **kw):
        rule, tab = self.rule_tab(DefaultKRule, **kw)
        tab.branch().extend(self.ngen(n))
        return (rule, tab)

    def test_rule_sentence_impl(self):
        rule, tab = self.case1()
        
        # tab.step()

@using(logic = 'CPL')
class TestTestDecorator(BaseSuite):

    def test_using_initial(self):
        assert self.logic.name == 'CPL'

    @using(logic = 'FDE')
    def test_using(self):
        assert self.logic.name == 'FDE'

    def test_using_restore(self):
        assert self.logic.name == 'CPL'
    