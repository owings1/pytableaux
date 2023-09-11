# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
# pytableaux.proof.tableaux tests
from __future__ import annotations

import time
from unittest import skip

from pytableaux.errors import *
from pytableaux.examples import arguments as examples
from pytableaux.lang import Argument
from pytableaux.proof import *
from pytableaux.proof import rules
from pytableaux.proof.filters import getkey
from pytableaux.proof.helpers import *
from pytableaux.proof.tableaux import *

from ..utils import BaseCase as Base


class TestSystem(Base):

    def test_build_trunk_base_not_impl(self):
        proof = Tableau()
        with self.assertRaises(NotImplementedError):
            System.build_trunk(proof, None)

class TestTableau(Base):

    logic = 'CPL'

    def test_step_returns_empty_when_finished(self):
        self.assertFalse(Tableau().finish().step())

    def test_repr_contains_finished(self):
        self.assertIn('finished', self.tab('Addition').__repr__())

    def test_build_premature_max_steps(self):
        self.assertTrue(self.tab('Material Modus Ponens', max_steps=1).premature)

    def test_construct_sets_is_rank_optim_option(self):
        tab = self.tab(is_rank_optim=False)
        self.assertTrue(tab.rules.get('Conjunction'))
        self.assertFalse(tab.opts['is_rank_optim'])

    def test_timeout_1ms(self):
        proof = self.tab('Addition', is_build=False, build_timeout=1)
        with proof.timers.build:
            time.sleep(0.005)
        with self.assertRaises(ProofTimeoutError):
            proof.build()

    def test_finish_empty_sets_build_duration_ms_0(self):
        self.assertEqual(Tableau().finish().stats['build_duration_ms'], 0)

    def test_add_closure_rule_instance_mock(self):
        class MockRule(rules.ClosingRule):
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
        tab = self.tab('Triviality 1', is_build_models=True)
        tab.build()
        self.assertTrue(tab.tree.model_id)


    def test_after_branch_add_with_nodes_no_parent(self):

        class MockRule(rules.NoopRule):

            __slots__ = '_checkbranch', '_checkparent'

            def __init__(self, *args, **opts):
                super().__init__(*args, **opts)
                def after_branch_add(branch: Branch):
                    self._checkbranch = branch
                    self._checkparent = branch.parent
                self.tableau.on(Tableau.Events.AFTER_BRANCH_ADD, after_branch_add)

        b = Branch().append({'test': True})
        tab = Tableau()
        tab.rules.append(MockRule)
        tab.add(b)

        rule = tab.rules.get(MockRule)
        self.assertIs(rule._checkbranch, b)
        self.assertIs(rule._checkparent, None)

    def test_ticked_step_flag_refactored_from_node(self):
        tab = self.tab()
        b = tab.branch()
        b += map(self.snode, ('NNa', 'Kab', 'Aab'))
        step = tab.step()
        stat = tab.stat(b, step.target.node, Tableau.StatKey.FLAGS)
        self.assertIn(Tableau.Flag.TICKED, stat)

    def test_raises_illegal_state_set_argument_started(self):
        tab = self.tab('Addition')
        with self.assertRaises(IllegalStateError):
            tab.argument = examples['DeMorgan 1']

    def test_raises_illegal_state_set_logic_started(self):
        tab = self.tab('Addition')
        with self.assertRaises(IllegalStateError):
            tab.logic = 'K'

    def test_auto_build_trunk_1(self):
        tab = self.tab()
        tab.argument = examples['Addition']
        self.assertTrue(len(tab))

    def test_auto_build_trunk_2(self):
        tab = Tableau(None, examples['Addition'])
        tab.logic = 'K'
        self.assertTrue(len(tab))

    def test_build_trunk_raises_no_arg(self):
        tab = self.tab()
        with self.assertRaises(IllegalStateError):
            tab.build_trunk()

    def test_build_trunk_raises_no_logic(self):
        tab = Tableau(None, examples['Addition'])
        with self.assertRaises(IllegalStateError):
            tab.build_trunk()

    def test_build_trunk_raises_already_built(self):
        tab = self.tab('Addition', is_build=False, auto_build_trunk=False)
        tab.build_trunk()
        with self.assertRaises(IllegalStateError):
            tab.build_trunk()

    def test_build_trunk_raises_already_started(self):
        tab = self.tab('Addition', is_build=False, auto_build_trunk=False)
        b = tab.branch()
        b += {'sentence': self.p('Kab')}
        entry = tab.step()
        self.assertTrue(entry)
        with self.assertRaises(IllegalStateError):
            tab.build_trunk()

    def test_bool_true_empty(self):
        tab = self.tab()
        self.assertEqual(len(tab), 0)
        self.assertTrue(tab)
        self.assertIs(bool(tab), True)

    def test_add_branch_duplicate_raises(self):
        tab = self.tab()
        b = tab.branch()
        with self.assertRaises(ValueError):
            tab.add(b)

    def test_repr_premature(self):
        tab = self.tab('DeMorgan 8', max_steps=1)
        self.assertIn('premature', repr(tab))

    def test_repr_invalid(self):
        tab = self.tab('Triviality 1', max_steps=1)
        self.assertIn('invalid', repr(tab))

    
class TestBranchStat(Base):
    def test_view_coverage(self):
        stat = Tableau.BranchStat()
        stat.view()

class TestRule(Base):

    def test_base_not_impl_various(self):
        with self.assertRaises(TypeError):
            Rule(Tableau())
        tab = Tableau()
        rule = rules.NoopRule(tab)
        b = tab.branch()
        t = Target(branch=b)
        with self.assertRaises(NotImplementedError):
            Rule._apply(rule, t)
        self.assertEqual(list(Rule._get_targets(rule, b)), [])
        self.assertEqual(list(Rule.example_nodes(rule)), [])

    def test_lock_can_set_attr_if_not_locked(self):
        tab = Tableau()
        rule = rules.NoopRule(tab)
        rule.helpers = {}

    def test_lock_raises_if_already_locked(self):
        tab = Tableau()
        rule = rules.NoopRule(tab)
        rule.lock()
        with self.assertRaises(IllegalStateError):
            rule.lock()

    def test_lock_raises_set_attr_if_locked(self):
        tab = Tableau()
        rule = rules.NoopRule(tab)
        rule.lock()
        with self.assertRaises(AttributeError):
            rule.helpers = {}

    def test_test_passes_with_noassert(self):
        rules.NoopRule.test(noassert=True)

    def test_test_passes_with_target(self):
        class RuleImpl(rules.NoopRule):
            def _get_targets(self, branch: Branch):
                yield Target(branch=branch)
        RuleImpl.test()

    def test_test_fails_with_assert(self):
        with self.assertRaises(AssertionError):
            rules.NoopRule.test()

    def test_repr_is_string_coverage(self):
        self.assertIs(type(repr(rules.NoopRule(Tableau()))), str)


class TestRuleGroup(Base):

    def test_contains_name(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.append(rules.NoopRule)
        self.assertIn('NoopRule', group)

    def test_names_has_rule_name(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.append(rules.NoopRule)
        self.assertIn('NoopRule', group.names())

    def test_contains_class(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.append(rules.NoopRule)
        self.assertIn(rules.NoopRule, group)

    def test_contains_instance(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.append(rules.NoopRule)
        self.assertIn(group[0], group)

    def test_contains_type_error_for_int(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        with self.assertRaises(TypeError):
            1 in group

    def test_repr_coverage(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        self.assertIs(type(repr(group)), str)

    def test_lock_can_clear_if_not_locked(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.append(rules.NoopRule)
        self.assertEqual(len(group), 1)
        group.clear()
        self.assertEqual(len(group), 0)

    def test_lock_raises_if_already_locked(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.lock()
        with self.assertRaises(IllegalStateError):
            group.lock()

    def test_lock_raises_clear_if_locked(self):
        group = RuleGroup(None, RulesRoot(Tableau()))
        group.lock()
        with self.assertRaises(IllegalStateError):
            group.clear()

class TestRuleGroups(Base):

    def test_append_iterable_rule_type(self):
        groups = RuleGroups(RulesRoot(Tableau()))
        groups.append(iter([rules.NoopRule]))
        self.assertIn(groups[0], groups)
        self.assertEqual(len(groups), 1)

    def test_extend_iterable_iterable_rule_type(self):
        groups = RuleGroups(RulesRoot(Tableau()))
        groups.extend(iter([iter([rules.NoopRule])]))
        self.assertIn(groups[0], groups)
        self.assertEqual(len(groups), 1)

    def test_get_raises_keyerror_no_default(self):
        groups = RuleGroups(RulesRoot(Tableau()))
        with self.assertRaises(KeyError):
            groups.get(rules.NoopRule)

    def test_names_has_group_name(self):
        groups = RuleGroups(RulesRoot(Tableau()))
        groups.append(iter([rules.NoopRule]), name='testname')
        self.assertIn('testname', groups.names())

    def test_lock_raises_if_already_locked(self):
        groups = RuleGroups(RulesRoot(Tableau()))
        groups.lock()
        with self.assertRaises(IllegalStateError):
            groups.lock()

    def test_repr_is_string_coverage(self):
        self.assertIs(type(repr(RuleGroups(RulesRoot(Tableau())))), str)

class TestRulesRoot(Base):

    class Rule1(rules.NoopRule): pass
    class Rule2(rules.NoopRule): pass
    class Rule3(rules.NoopRule): pass

    def test_len_0_then_1_then_2(self):
        root = RulesRoot(Tableau())
        self.assertEqual(len(root), 0)
        root.append(self.Rule1)
        self.assertEqual(len(root), 1)
        root.append(self.Rule2)
        self.assertEqual(len(root), 2)

    def test_getitem(self):
        root = RulesRoot(Tableau())
        root.append(self.Rule1)
        root.extend([self.Rule2, self.Rule3])
        self.assertEqual(type(root[0]), self.Rule1)
        self.assertEqual(type(root[1]), self.Rule2)
        self.assertEqual(type(root[2]), self.Rule3)
        self.assertEqual(type(root[-3]), self.Rule1)
        self.assertEqual(type(root[-2]), self.Rule2)
        self.assertEqual(type(root[-1]), self.Rule3)

    def test_repr_is_string_coverage(self):
        root = RulesRoot(Tableau())
        self.assertIs(type(repr(root)), str)

    def test_duplicate_key(self):
        root = RulesRoot(Tableau())
        root.append(self.Rule1)
        class Rule1(rules.NoopRule): pass
        with self.assertRaises(KeyError):
            root.append(Rule1)

    def test_reversed(self):
        root = RulesRoot(Tableau())
        root.append(self.Rule1)
        root.groups.append([self.Rule2, self.Rule3])
        exp = [self.Rule3, self.Rule2, self.Rule1]
        res = list(map(type, reversed(root)))
        self.assertEqual(res, exp)

    def test_lock_raises_already_locked(self):
        root = RulesRoot(Tableau())
        root.lock()
        with self.assertRaises(IllegalStateError):
            root.lock()

class TestClosureRule(Base):

    def test_base_not_impl_various(self):
        with self.assertRaises(TypeError):
            ClosingRule(Tableau())

class TestFilters(Base):


    def test_AttrFilter_key_node_designated(self):
        class Lhs(object):
            testname = True
        class AttrFilt(filters.CompareAttr):
            attrmap = {'testname': 'designated'}
            rget = staticmethod(getkey)
        f = AttrFilt(Lhs())
        assert f(Node.for_mapping({'designated': True}))
        assert not f(Node({'foo': 'bar'}))


class TestEllispsisHelper(Base):

    logic = 'FDE'

    def test_closing_rule_ellipsis(self):

        tab = self.tab()
        rule = tab.rules.get('DesignationClosure')
        helper = helpers.EllipsisExampleHelper(rule)
        rule.helpers[helpers.EllipsisExampleHelper] = helper
        b = tab.branch().extend(rule.example_nodes())
        tab.build()
        node = b.find(helper.mynode)
        self.assertIsNot(node, None)
        self.assertEqual(len(b), 4)
        self.assertIs(node, b[1])

class TestMaxConstantsTracker(Base):

    logic = 'S5'

    def test_argument_trunk_two_qs_returns_3(self):
    
        class FilterNodeRule(rules.NoopRule):
            Helpers = FilterHelper,
            ignore_ticked = None
    
        class MtrTestRule(FilterNodeRule):
            Helpers = MaxConsts,
    
        proof = self.tab()
        proof.rules.append(MtrTestRule)
        proof.argument = Argument('NLVxNFx:LMSxFx')
        rule = proof.rules.get(MtrTestRule)
        branch = proof[0]
        self.assertEqual(rule[MaxConsts]._compute(branch), 3)

    @skip(None)
    def xtest_compute_for_node_one_q_returns_1(self):
        n = {'sentence': self.p('VxFx'), 'world': 0}
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
        n1 = {'sentence': s1, 'world': 0}
        n2 = {'sentence': s2, 'world': 0}
        proof = Tableau()
        rule = Rule(proof)
        branch = proof.branch()
        branch.extend([n1, n2])
        res = rule[MaxConsts]._compute_max_constants(branch)
        self.assertEqual(res, 3)




class TestSystem(Base):


    def test_branch_complexity_hashable_none_if_no_sentence(self):
        n = Node({})
        self.assertIs(None, System.branching_complexity_hashable(n))

    def test_branch_complexity_0_if_no_sentence(self):
        tab = Tableau()
        n = Node({})
        self.assertEqual(0, System.branching_complexity(n, tab.rules))
class TestRules(Base):

    def test_abstract_default_node_rule(self):
        class Impl(rules.DefaultNodeRule, intermediate=True): pass
        rule = rules.NoopRule(Tableau())
        with self.assertRaises(NotImplementedError):
            Impl._get_sd_targets(rule, Node({}), Branch())

    def test_abstract_operator_node_rule(self):
        class Impl(rules.OperatorNodeRule): pass
        with self.assertRaises(TypeError):
            Impl(Tableau())
        rule = rules.NoopRule(Tableau())
        with self.assertRaises(NotImplementedError):
            Impl._get_sd_targets(rule, Node({}), Branch())

    def test_notimpl_coverage(self):
        rule = rules.NoopRule(Tableau())
        with self.assertRaises(NotImplementedError):
            rules.OperatorNodeRule._get_sd_targets(rule, self.p('a'), False)
