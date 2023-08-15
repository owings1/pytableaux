from __future__ import annotations

import time
from pytableaux import examples
from pytableaux.errors import *
from pytableaux.lang.lex import Atomic, Constant, Predicated
from pytableaux.logics.k import DefaultNodeRule as DefaultKRule
from pytableaux.proof import TableauxSystem as TabSys
from pytableaux.proof import filters
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.filters import getkey
from pytableaux.proof.helpers import *
from pytableaux.proof.rules import ClosingRule, NoopRule, Rule
from pytableaux.proof.tableaux import Tableau
from types import MappingProxyType as MapProxy
from pytest import raises
from unittest import skip
from . import BaseCase



exarg = examples.argument
sen = 'sentence'


class TestTableauxSystem(BaseCase):

    def test_build_trunk_base_not_impl(self):
        proof = Tableau()
        with self.assertRaises(NotImplementedError):
            TabSys.build_trunk(proof, None)

class TestTableau(BaseCase):

    logic = 'CPL'

    def test_step_returns_false_when_finished(self):
        self.assertFalse(Tableau().finish().step())

    def test_repr_contains_finished(self):
        self.assertIn('finished', self.tab('Addition').__repr__())

    def test_build_premature_max_steps(self):
        self.assertTrue(self.tab('MMP', max_steps=1).premature)

    def test_construct_sets_is_rank_optim_option(self):
        tab = self.tab(is_rank_optim=False)
        self.assertTrue(tab.rules.get('Conjunction'))
        self.assertFalse(tab.opts['is_rank_optim'])

    def test_timeout_1ms(self):
        proof = Tableau('cpl', exarg('Addition'), build_timeout=1)
        with proof.timers.build:
            time.sleep(0.005)
        with raises(ProofTimeoutError):
            proof.build()

    def test_finish_empty_sets_build_duration_ms_0(self):
        self.assertEqual(Tableau().finish().stats['build_duration_ms'], 0)

    def test_add_closure_rule_instance_mock(self):
        class MockRule(ClosingRule):
            def _get_targets(self, branch: Branch):
                return Target(branch = branch),
            def nodes_will_close_branch(self, nodes, branch):
                return True
            def example_nodes(self):
                return {},
        tab = Tableau()
        tab.rules.append(MockRule)
        tab.branch()
        self.assertEqual(len(tab.open), 1)
        tab.build()
        self.assertEqual(len(tab.open), 0)

    def test_regress_structure_has_model_id(self):
        tab = Tableau('CPL', exarg('Triviality 1'), is_build_models=True)
        tab.build()
        self.assertTrue(tab.tree.model_id)


    def test_after_branch_add_with_nodes_no_parent(self):

        class MockRule(NoopRule):

            __slots__ = '__dict__',
            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                self.tableau.on(Tableau.Events.AFTER_BRANCH_ADD, self.__after_branch_add)

            def __after_branch_add(self, branch: Branch):
                self._checkbranch = branch
                self._checkparent = branch.parent

        b = Branch().append({'test': True})
        tab = Tableau()
        tab.rules.append(MockRule)
        tab.add(b)

        rule = tab.rules.get(MockRule)
        self.assertIs(rule._checkbranch, b)
        self.assertIs(rule._checkparent, None)

    def test_ticked_step_flag_refactored_from_node(self):
        sen = 'sentence'
        tab, b = self.tabb([
            {sen: s} for s in self.pp('NNa', 'Kab', 'Aab')
        ])
        step = tab.step()
        stat = tab.stat(b, step.target.node, Tableau.StatKey.FLAGS)
        self.assertIn(Tableau.Flag.TICKED, stat)

class TestBranch(BaseCase):

    def test_next_world_returns_w0(self):
        self.assertEqual(Branch().new_world(), 0)

    def test_new_constant_returns_m(self):
        self.assertEqual(Branch().new_constant(), Constant(0, 0))

    def test_new_constant_returns_m1_after_s0(self):
        b = Branch()
        i = 0
        while i <= Constant.TYPE.maxi:
            c = Constant(i, 0)
            sen = Predicated('Identity', (c, c))
            b.append({'sentence': sen})
            i += 1
        self.assertEqual(b.new_constant(), Constant(0, 1))

    def test_repr_contains_closed(self):
        self.assertIn('closed', Branch().__repr__())

    def test_has_all_true_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{sen: s1}, {sen: s2}, {sen: s3}])
        check = [{sen: s1, sen: s2}]
        self.assertTrue(b.all(check))

    def test_has_all_false_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{sen: s1}, {sen: s3}])
        check = [{sen: s1, sen: s2}]
        self.assertFalse(b.all(check))

    def test_branch_has_world1(self):
        proof = Tableau()
        branch = proof.branch().append({'world1': 4, 'world2': 1})
        self.assertTrue(branch.has({'world1': 4}))


    def test_regression_branch_has_works_with_newly_added_node_on_after_node_add(self):

        class MyRule(NoopRule):

            __slots__ = 'should_be', 'shouldnt_be'

            def __init__(self, *args, **opts):
                self.should_be = False
                self.shouldnt_be = True
                super().__init__(*args, **opts)
                self.tableau.on(Tableau.Events.AFTER_NODE_ADD, self.__after_node_add)

            def __after_node_add(self, node: Node, branch: Branch):
                self.should_be = branch.has({'world1': 7})
                self.shouldnt_be = branch.has({'world1': 6})

        proof = Tableau()
        proof.rules.append(MyRule)
        rule = proof.rules.get(MyRule)
        proof.branch().append({'world1': 7})

        self.assertTrue(rule.should_be)
        self.assertFalse(rule.shouldnt_be)


    def test_select_index_non_indexed_prop(self):
        branch = Branch()
        branch.append({'foo': 'bar'})
        idx = branch._index.select({'foo': 'bar'}, branch)
        self.assertEqual(list(idx), list(branch))

    def test_select_index_access(self):
        b = Branch()
        b.extend((
            {'world1': 0, 'world2': 1},
            *({'foo': 'bar'} for _ in range(len(b._index))),
        ))
        base = b._index.select({'world1': 0, 'world2': 1}, b)
        self.assertEqual(set(base), {b[0]})

    def test_close_adds_flag_node(self):
        branch = Branch()
        branch.close()
        self.assertTrue(branch.has({'is_flag': True, 'flag': 'closure'}))


    # def test_constants_or_new_returns_pair_no_constants(self):
    #     branch = Branch()
    #     res = branch.constants_or_new()
    #     self.assertEqual(len(res), 2)
    #     constants, is_new = res
    #     self.assertEqual(len(constants), 1)
    #     assert is_new

    # def test_constants_or_new_returns_pair_with_constants(self):
    #     branch = Branch()
    #     s1 = Predicated('Identity', [Constant(0, 0), Constant(1, 0)])
    #     branch.append({sen: s1})
    #     res = branch.constants_or_new()
    #     self.assertEqual(len(res), 2)
    #     constants, is_new = res
    #     self.assertEqual(len(constants), 2)
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
        self.assertEqual(tuple(n for n in iter(b)), nn)
        self.assertEqual(tuple(n for n in b), nn)
        self.assertEqual(tuple(dict(n) for n in iter(b)), npp)
        self.assertEqual(tuple(dict(n) for n in b), npp)

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

        self.assertEqual(len(branch), len(nodes))
        self.assertEqual(len(branch), size)

        # indexes
        it = gen(
            0, -1
        )

        for a, b in it:
            self.assertIs(a, b)
            self.assertEqual(branch.index(a), nodes.index(b))

        # slices
        it = gen(
            (0, 1), (2, -1), (3, None)
        )

        for a, b in it:
            self.assertEqual(list(a), list(b))


    def test_create_list_tuple_set_from_branch(self):
        b, nn = self.case1(5)
        nodes = list(b)
        self.assertEqual(tuple(b), nn)
        self.assertEqual(set(b), set(nn))
        self.assertEqual(nodes, list(nn))
        self.assertEqual(len(nodes), len(b))
        self.assertEqual(len(nodes), 5)

    def case2(self, n = 2):
        return Branch().extend(self.nn1(n=n))

    def test_subscript_errors(self):
        b = self.case2()
        with raises(TypeError):
            b['0']
        with raises(IndexError):
            b[2]

    def test_len_0_6(self):
        self.assertEqual(len(self.case2(0)), 0)
        self.assertEqual(len(self.case2(6)), 6)


class TestNode(BaseCase):

    def test_worlds_contains_worlds(self):
        node = Node.for_mapping({'world1': 0, 'world2': 1})
        res = set(node.worlds())
        self.assertIn(0, res)
        self.assertIn(1, res)

    def test_clousre_flag_node_has_is_flag(self):
        branch = Branch()
        branch.close()
        node = branch[0]
        assert node.has('is_flag')

    def test_create_node_with_various_types(self):
        exp = {}
        exp.update({'a':1,'b':2,'c':3})
        for inp in [
            dict(zip(('a', 'b', 'c'), (1, 2, 3))),
            MapProxy(exp),
        ]:
            self.assertEqual(dict(Node(inp)), exp)

    def test_or_ror_operators(self):
        pa = dict(world = None, designated = None)
        pb = pa.copy()
        pa.update({'a': 1, 'b': 3, 'C': 3, 'x': 1})
        pb.update({'A': 1, 'b': 2, 'c': 4, 'y': 3})
        exp1 = pa | pb
        exp2 = pb | pa
        n1, n2 = map(Node, (pa, pb))
        self.assertEqual(n1 | n2, exp1)
        self.assertEqual(n1 | dict(n2), exp1)
        self.assertEqual(dict(n1) | n2, exp1)
        self.assertEqual(dict(n1) | dict(n2), exp1)
        self.assertEqual(n2 | n1, exp2)
        self.assertEqual(n2 | dict(n1), exp2)
        self.assertEqual(dict(n2) | n1, exp2)
        self.assertEqual(dict(n2) | dict(n1), exp2)
        
class TestRule(BaseCase):

    def test_base_not_impl_various(self):
        with raises(TypeError):
            Rule(Tableau())

class TestClosureRule(BaseCase):

    def test_base_not_impl_various(self):
        with raises(TypeError):
            ClosingRule(Tableau())

class TestFilters(BaseCase):


    def test_AttrFilter_key_node_designated(self):
        class Lhs(object):
            testname = True
        class AttrFilt(filters.CompareAttr):
            attrmap = {'testname': 'designated'}
            rget = staticmethod(getkey)
        f = AttrFilt(Lhs())
        assert f(Node.for_mapping({'designated': True}))
        assert not f(Node({'foo': 'bar'}))


class TestEllispsisHelper(BaseCase):

    logic = 'FDE'

    def test_closing_rule_ellipsis(self):
        import os.path
        import sys
        addpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../doc'))
        sys.path.append(addpath)
        from pytabdoc.misc import EllipsisExampleHelper as Rcls # type: ignore
        sys.path.pop()
        tab = self.tab()
        rule = tab.rules.get('DesignationClosure')
        helper = Rcls(rule)
        rule.helpers[Rcls] = helper
        b = tab.branch().extend(rule.example_nodes())
        tab.build()
        node = b.find(helper.mynode)
        self.assertIsNot(node, None)
        self.assertEqual(len(b), 4)
        self.assertIs(node, b[1])

class Test_K_DefaultNodeFilterRule(BaseCase):

    logic = 'K'

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
            yield Node.for_mapping(n)
        sgen.close()

    def case1(self, n = 10, **kw):
        class Impl(DefaultKRule):
            def _get_node_targets(self, node, branch): pass
        rule, tab = self.rule_tab(Impl, **kw)
        tab.branch().extend(self.ngen(n))
        return (rule, tab)

    def test_rule_sentence_impl(self):
        rule, tab = self.case1()


class TestMaxConstantsTracker(BaseCase):

    logic = 'S5'

    def test_argument_trunk_two_qs_returns_3(self):
    
        class FilterNodeRule(NoopRule):
            Helpers = FilterHelper,
            ignore_ticked = None
    
        class MtrTestRule(FilterNodeRule):
            Helpers = MaxConsts,
    
        proof = self.tab()
        proof.rules.append(MtrTestRule)
        proof.argument = self.parg('NLVxNFx', 'LMSxFx')
        rule = proof.rules.get(MtrTestRule)
        branch = proof[0]
        self.assertEqual(rule[MaxConsts]._compute(branch), 3)

    @skip(None)
    def xtest_compute_for_node_one_q_returns_1(self):
        n = {sen: self.p('VxFx'), 'world': 0}
        node = Node.for_mapping(n)
        proof = Tableau()
        rule = Rule(proof)
        branch = proof.branch()
        branch.append(node)
        res = rule[MaxConsts]._compute_needed_constants_for_node(node, branch)
        self.assertEqual(res, 1)

    @skip(None)
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
        self.assertEqual(res, 3)



class TestKNewExistential(BaseCase):

    logic = 'K'

    def test_rule_applies(self):
        rule, tab = self.rule_eg('Existential', bare = True)

class TestKNewUniversal(BaseCase):

    logic = 'K'

    def test_rule_applies(self):
        rule, tab = self.rule_eg('Universal', bare = True)
