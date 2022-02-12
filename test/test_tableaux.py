from __future__ import annotations

from errors import *
from tools.abcs import MapProxy
from tools.callables import calls, gets
from tools.misc import get_logic

from lexicals import Atomic, Constant, Predicated, Quantifier as Quant

from proof.tableaux import (
    Rule, TableauxSystem as TabSys, Tableau,
    ClosingRule, RuleT
)
from proof.filters import Filters
from proof.helpers import AdzHelper, FilterHelper, MaxConsts
from proof.common import Branch, Node, Target
from proof.types import TabEvent, TabStatKey, TabFlag
import examples

import time
from pytest import raises
from typing import TypeVar

from .tutils import BaseSuite, using, skip


def mock_sleep_5ms():
    time.sleep(0.005)

exarg = examples.argument
sen = 'sentence'

class RuleStub(Rule):
    def _apply(self, target): pass
    def _get_targets(self, branch): pass
    def example_nodes(self): return tuple()

class TestTableauxSystem(BaseSuite):

    def test_build_trunk_base_not_impl(self):
        proof = Tableau()
        with raises(NotImplementedError):
            TabSys.build_trunk(proof, None)

@using(logic = 'CPL')
class TestTableau(BaseSuite):

    def test_step_returns_false_when_finished(self):
        assert Tableau().finish().step() == False

    def test_repr_contains_finished(self):
        assert 'finished' in self.tab('Addition').__repr__()

    def test_build_premature_max_steps(self):
        assert self.tab('MMP', max_steps=1).premature

    def test_construct_sets_is_rank_optim_option(self):
        tab = self.tab(is_rank_optim=False)
        assert tab.rules.get('Conjunction')
        assert not tab.opts['is_rank_optim']

    def test_timeout_1ms(self):
        proof = Tableau('cpl', exarg('Addition'), build_timeout=1)
        proof.step = mock_sleep_5ms
        with raises(TimeoutError):
            proof.build()

    def test_finish_empty_sets_build_duration_ms_0(self):
        assert Tableau().finish().stats['build_duration_ms'] == 0

    def test_add_closure_rule_instance_mock(self):
        class MockRule(ClosingRule):
            def _get_targets(self, branch: Branch):
                return Target(branch = branch),
            def node_will_close_branch(self, node, branch):
                return True
            def example_nodes(self):
                return {},
        tab = Tableau()
        tab.rules.append(MockRule)
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

    def test_after_branch_add_with_nodes_no_parent(self):

        class MockRule(RuleStub):

            __slots__ = '__dict__',
            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                self.tableau.on(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)

            def __after_branch_add(self, branch: Branch):
                self._checkbranch = branch
                self._checkparent = branch.parent

        b = Branch().add({'test': True})
        tab = Tableau()
        tab.rules.append(MockRule)
        tab.add(b)

        rule = tab.rules.get(MockRule)
        assert rule._checkbranch is b
        assert rule._checkparent == None

    def test_ticked_step_flag_refactored_from_node(self):
        sen = 'sentence'
        tab, b = self.tabb([
            {sen: s} for s in self.pp('NNa', 'Kab', 'Aab')
        ])
        step = tab.step()
        stat = tab.stat(b, step.target.node, TabStatKey.FLAGS)
        assert TabFlag.TICKED in stat

class TestBranch:

    def test_next_world_returns_w0(self):
        assert Branch().next_world == 0

    def test_new_constant_returns_m(self):
        assert Branch().new_constant() == Constant(0, 0)

    def test_new_constant_returns_m1_after_s0(self):
        b = Branch()
        i = 0
        while i <= Constant.TYPE.maxi:
            c = Constant(i, 0)
            sen = Predicated('Identity', (c, c))
            b.add({'sentence': sen})
            i += 1
        assert b.new_constant() == Constant(0, 1)

    def test_repr_contains_closed(self):
        assert 'closed' in Branch().__repr__()

    def test_has_all_true_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{sen: s1}, {sen: s2}, {sen: s3}])
        check = [{sen: s1, sen: s2}]
        assert b.has_all(check)

    def test_has_all_false_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{sen: s1}, {sen: s3}])
        check = [{sen: s1, sen: s2}]
        assert not b.has_all(check)

    def test_branch_has_world1(self):
        proof = Tableau()
        branch = proof.branch().add({'world1': 4, 'world2': 1})
        assert branch.has({'world1': 4})

    # def test_append_existing_node_fails(self):
    #     b, n = Branch(), Node()
    #     b.append(n)
    #     assert len(b) == 1 and n in b
    #     with raises(ValueError):
    #         b.append(n)

    def test_regression_branch_has_works_with_newly_added_node_on_after_node_add(self):

        class MyRule(RuleStub):

            __slots__ = 'should_be', 'shouldnt_be'

            def __init__(self, *args, **opts):
                self.should_be = False
                self.shouldnt_be = True
                super().__init__(*args, **opts)
                self.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)

            def __after_node_add(self, node: Node, branch: Branch):
                self.should_be = branch.has({'world1': 7})
                self.shouldnt_be = branch.has({'world1': 6})

        proof = Tableau()
        proof.rules.append(MyRule)
        rule = proof.rules.get(MyRule)
        proof.branch().add({'world1': 7})

        assert rule.should_be
        assert not rule.shouldnt_be


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
    #     branch.add({sen: s1})
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
        if nn is None:
            nn = self.nn1(n)
        b.extend(nn)
        return (b, nn)

    def test_for_in_iter_nodes(self):
        b, nn = self.case1()
        npp = tuple(dict(n) for n in nn)
        assert tuple(n for n in iter(b)) == nn
        assert tuple(n for n in b) == nn
        assert tuple(dict(n) for n in iter(b)) == npp
        assert tuple(dict(n) for n in b) == npp

    def gcase1(self, *a, **k):
        b, nn = self.case1(*a, *k)
        def gen(*subs):
            for i in subs:
                if not isinstance(i, int):
                    i = slice(*i)
                yield b[i], nn[i]
        return gen, b, nn

    def test_subscript_1(self):
        size = 5
        gen, branch, nodes = self.gcase1(size)

        assert len(branch) == len(nodes)
        assert len(branch) == size

        # indexes
        it = gen(
            0, -1
        )

        for a, b in it:
            assert a is b
            assert branch.index(a) == nodes.index(b)

        # slices
        it = gen(
            (0, 1), (2, -1), (3, None)
        )

        for a, b in it:
            assert list(a) == list(b)


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

    def test_subscript_errors(self):
        b = self.case2()
        with raises(TypeError):
            b['0']
        with raises(IndexError):
            b[2]

    def test_len_0_6(self):
        assert len(self.case2(0)) == 0
        assert len(self.case2(6)) == 6


class TestNode:

    def test_worlds_contains_worlds(self):
        node = Node({'worlds': {0, 1}})
        res = node.worlds
        assert 0 in res
        assert 1 in res

    def test_clousre_flag_node_has_is_flag(self):
        branch = Branch()
        branch.close()
        node = branch[0]
        assert node.has('is_flag')

    def test_create_node_with_various_types(self):
        exp = {}
        exp.update({'a':1,'b':2,'c':3})
        for inp in [
            zip(('a', 'b', 'c'), (1, 2, 3)),
            MapProxy(exp),
            exp.items()
        ]:
            assert dict(Node(inp)) == exp

    def test_or_ror_operators(self):
        pa = dict(world = None, designated = None)
        pb = pa.copy()
        pa.update({'a': 1, 'b': 3, 'C': 3, 'x': 1})
        pb.update({'A': 1, 'b': 2, 'c': 4, 'y': 3})
        exp1 = pa | pb
        exp2 = pb | pa
        n1, n2 = map(Node, (pa, pb))
        assert n1 | n2 == exp1
        assert n1 | dict(n2) == exp1
        assert dict(n1) | n2 == exp1
        assert dict(n1) | dict(n2) == exp1
        assert n2 | n1 == exp2
        assert n2 | dict(n1) == exp2
        assert dict(n2) | n1 == exp2
        assert dict(n2) | dict(n1) == exp2
        
class TestRule(BaseSuite):

    def test_base_not_impl_various(self):
        with raises(TypeError):
            Rule(Tableau())

class TestClosureRule(BaseSuite):

    def test_base_not_impl_various(self):
        with raises(TypeError):
            ClosingRule(Tableau())

class TestFilters(BaseSuite):

    def test_AttrFilter_node_is_modal(self):
        class Lhs(object):
            testname = True
        class AttrFilt(Filters.Attr):
            attrmap = {'testname': 'is_modal'}
        f = AttrFilt(Lhs())
        assert f(Node({'world1': 0}))
        assert not f(Node({'foo': 'bar'}))

    def test_AttrFilter_key_node_designated(self):
        class Lhs(object):
            testname = True
        class AttrFilt(Filters.Attr):
            attrmap = {'testname': 'designated'}
        f = AttrFilt(Lhs())
        f.rget = gets.key()
        assert f(Node({'designated': True}))
        assert not f(Node({'foo': 'bar'}))


from logics.k import DefaultNodeRule as DefaultKRule

@using(logic = 'K')
class Test_K_DefaultNodeFilterRule(BaseSuite):

    def ngen(self, n):
        sgen = self.sgen(n)
        wn = 0
        for i in range(n):
            s = next(sgen)
            if i == 0:
                n = {sen:s}
            elif i % 3 == 0:
                w1 = wn
                w2 = wn = w1 + 1
                n = {'world1':w1, 'world2':w2}
            else:
                n = {sen:s, 'world':wn}
            yield Node(n)
        sgen.close()

    def case1(self, n = 10, **kw):
        class Impl(DefaultKRule):
            def _get_node_targets(self, node, branch): pass
        rule, tab = self.rule_tab(Impl, **kw)
        tab.branch().extend(self.ngen(n))
        return (rule, tab)

    def test_rule_sentence_impl(self):
        rule, tab = self.case1()

@using(logic = 'S5')
class TestMaxConstantsTracker(BaseSuite):

    def test_argument_trunk_two_qs_returns_3(self):
    
        class FilterNodeRule(RuleStub):
            Helpers = FilterHelper,
            ignore_ticked = None
    
        class MtrTestRule(FilterNodeRule):
            Helpers = (
                *FilterNodeRule.Helpers,
                MaxConsts,
            )
    
        proof = self.tab()
        proof.rules.append(MtrTestRule)
        proof.argument = self.parg('NLVxNFx', 'LMSxFx')
        rule = proof.rules.get(MtrTestRule)
        branch = proof[0]
        assert rule[MaxConsts]._compute_max_constants(branch) == 3

    @skip
    def xtest_compute_for_node_one_q_returns_1(self):
        n = {sen: self.p('VxFx'), 'world': 0}
        node = Node(n)
        proof = Tableau()
        rule = Rule(proof)
        branch = proof.branch()
        branch.add(node)
        res = rule[MaxConsts]._compute_needed_constants_for_node(node, branch)
        assert res == 1

    @skip
    def test_compute_for_branch_two_nodes_one_q_each_returns_3(self):
        s1 = self.p('LxFx')
        s2 = self.p('SxFx')
        n1 = {sen: s1, 'world': 0}
        n2 = {sen: s2, 'world': 0}
        proof = Tableau()
        rule = Rule(proof)
        branch = proof.branch()
        branch.extend([n1, n2])
        res = rule[MaxConsts]._compute_max_constants(branch)
        assert res == 3

@using(logic = 'CPL')
class TestTestDecorator(BaseSuite):

    def test_using_initial(self):
        assert self.logic.name == 'CPL'

    @using(logic = 'FDE')
    def test_using(self):
        assert self.logic.name == 'FDE'

    def test_using_restore(self):
        assert self.logic.name == 'CPL'

@using(logic = 'K')
class TestNewQuantifierRules(BaseSuite):

    class TestKNewExistential(BaseSuite):

        def test_rule_applies(self):
            rule, tab = self.rule_eg('Existential', bare = True)

    class TestKNewUniversal(BaseSuite):

        def test_rule_applies(self):
            rule, tab = self.rule_eg('Universal', bare = True)
