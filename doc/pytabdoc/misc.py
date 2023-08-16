# -*- coding: utf-8 -*-
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
"""
pytabdoc.misc
^^^^^^^^^^^^^

"""
from __future__ import annotations

import enum
import re
from collections import defaultdict, deque
from inspect import getsource
from typing import Any, Collection

from sphinx.ext.autodoc.importer import import_object

from pytableaux.lang import LexType
from pytableaux.logics import LogicType, registry
from pytableaux.proof import (Branch, ClosingRule, ClosureNode, Node, Rule,
                              Tableau)
from pytableaux.proof import System as TabSys
from pytableaux.proof import Target
from pytableaux.proof.filters import CompareSentence
from pytableaux.tools.abcs import isabstract

__all__ = (
    'EllipsisExampleHelper',
    'get_logic_names',
    'is_concrete_build_trunk',
    'is_concrete_rule',
    'is_rule_class',
    'is_transparent_rule')


def is_concrete_rule(obj: Any, /) -> bool:
    return is_rule_class(obj) and obj and not isabstract(obj)

def is_concrete_build_trunk(obj: Any, /,):
    return TabSys.build_trunk in _methmro(obj) and not isabstract(obj)

def is_transparent_rule(obj: Any) -> bool:
    """Whether a rule class:
        - is included in Rules groups for the module it belongs to
        - inherits from a rule class that belongs to another logic module
        - the parent class is in the other logic's rule goups
        - there is no implementation besides pass
        - there is no docblock
    """
    return (
        is_rule_class(obj) and
        _is_nodoc(obj) and
        _is_nocode(obj) and
        _rule_is_self_grouped(obj) and
        _rule_is_parent_grouped(obj))

def rules_sorted(logic: LogicType, rules = None, /) -> dict:
    logic = registry(logic)
    RulesCls = logic.Rules
    if rules is None:
        rules = list(RulesCls.all_rules)
    results = dict(
        member_order = rules_sorted_member_order(logic, rules),
        legend_groups = (groups := rules_grouped_legend_order(rules)),
        legend_order = [rule for group in groups.values() for rule in group],
        legend_subgroups = (subgrouped := rules_legend_subgroups(groups)),
        subgroups_named = {
            name: {o.name : [r.name for r in subgroup]for o, subgroup in group.items()}
            for name, group in subgrouped.items()},
        subgroup_types = {
            name: type(next(iter(group)))
            for name, group in subgrouped.items()
            if len(group)})
    return results

def rule_sortkey_legend(rule: type[Rule]):
    if (c := CompareSentence(rule).compitem) is None:
        if issubclass(rule, ClosingRule):
            return 0,
        return LexType._seq[-1].rank + 1,
    return (c.item, bool(getattr(c, 'negated', 0)),
        -1 * bool(getattr(rule, 'designation', None)))

def rules_grouped_legend_order(rules: Collection[type[Rule]], /) -> dict:
    groups = {name: [] for name in ('closure', 'operator', 'quantifier', 'predicate')}
    ungrouped = []
    for rule in rules:
        for name, _ in rule.legend:
            if name in groups:
                groups[name].append(rule)
                break
        else:
            ungrouped.append(rule)
    for name in ('operator', 'quantifier', 'predicate'):
        groups[name].sort(key = rule_sortkey_legend)
    groups['ungrouped'] = ungrouped
    return groups

def rules_legend_subgroups(groups: dict[str, list[type[Rule]]]) -> dict:
    subgroups: dict[str, dict[Any, list]] = {
        name: {}
        for name in ('operator', 'quantifier', 'predicate')}
    for name, group in groups.items():
        if name in subgroups:
            subgroup = subgroups[name]
            for rule in group:
                obj = getattr(rule, name)
                if obj not in subgroup:
                    subgroup[obj] = []
                subgroup[obj].append(rule)
    return subgroups

def rules_sorted_member_order(logic: LogicType, rules: Collection[type[Rule]], /) -> list[type[Rule]]:
    RulesCls = logic.Rules
    native_members = []
    todo = set(rules)
    for member in filter(is_rule_class, RulesCls.__dict__.values()):
        if member in todo:
            native_members.append(member)
            todo.remove(member)
    keys_member_order = {rule: i for i, rule in enumerate(native_members, 1)}
    inherit_map = defaultdict(set)
    for rule in todo:
        inherit_map[registry.locate(rule)].add(rule)
    for parent, values in inherit_map.items():
        others = rules_sorted_member_order(parent, values)
        inherit_map[parent] = others
        keys_member_order.update({
            rule: i
            for i, rule in enumerate(others, len(keys_member_order))})
    return sorted(rules, key = keys_member_order.__getitem__)
# ------------------------------------------------


def is_enum_member(modname: str, objpath = None):

    if objpath is not None:
        importinfo = import_object(modname, objpath[0:-1])

    else:
        fullpath = modname.split('.')
        if len(fullpath) < 3:
            return False
        objpath = [fullpath[-2], fullpath[-1]]
        modname = '.'.join(fullpath[0:-2])
        while len(modname):
            try:
                importinfo = import_object(modname, objpath[0:-1])
            except ImportError:
                parts = modname.split('.')
                objpath.insert(0, parts.pop())
                modname = '.'.join(parts)
            else:
                break
        else:
            return False

    importobj = importinfo[-1]
    if isinstance(importobj, type) and issubclass(importobj, enum.Enum):
        try:
            _ = importobj(objpath[-1])
        except (ValueError, TypeError) as e:
            return False
        else:
            return True


def is_rule_class(obj: Any) -> bool:
    'Wether obj is a rule class.'
    return isinstance(obj, type) and issubclass(obj, Rule)

def _is_nodoc(obj: Any) -> bool:
    return not bool(getattr(obj, '__doc__', None))

def _is_nocode(obj: Any) -> bool:
    'Try to determine if obj has no "effective" code.'
    isblock = False
    isfirst = True
    pat = rf'^(class|def) {obj.__name__}(\([a-zA-Z0-9_.]+\))?:$'
    try:
        it = filter(len, map(str.strip, getsource(obj).split('\n')))
    except:
        return False
    for line in it:
        if isfirst:
            isfirst = False
            m = re.findall(pat, line)
            if not m:
                return False
            continue
        if line.startswith('#'):
            continue
        if line == 'pass':
            continue
        if line.startswith('"""'):
            # not perfect, but more likely to produce false negatives
            # than false positives
            isblock = not isblock
            continue
        if isblock:
            continue
        return False
    return True

def _rule_is_grouped(rule: type[Rule], logic) -> bool:
    'Whether the rule class is grouped in the Rules of the given logic.'
    if not is_rule_class(rule):
        return False
    try:
        logic = registry.locate(logic)
    except:
        return False
    return rule in logic.Rules.all_rules

def _rule_is_self_grouped(rule: type[Rule]) -> bool:
    'Whether the Rule class is grouped in the Rules of its own logic.'
    logic = registry.locate(rule)
    return _rule_is_grouped(rule, logic)

def _rule_is_parent_grouped(rule: type[Rule]) -> bool:
    "Whether the Rule class's parent is grouped in its own logic."
    if not isinstance(rule, type):
        return False
    return _rule_is_self_grouped(rule.mro()[1])

def _methmro(meth: Any) -> list[str]:
    """Get the methods of the same name of the mro (safe) of the class the
    method is bound to."""
    try:
        it = (getattr(c, meth.__name__, None) for c in meth.__self__.__mro__)
    except:
        return []
    return list(filter(None, it))

class EllipsisExampleHelper(Rule.Helper):

    closenodes: list[Node]
    applied: set[Branch]
    isclosure: bool
    istrunk: bool
    mynode = Node.PropMap.Ellipsis

    __slots__ = ('__dict__',)

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        self.applied = set()
        self.isclosure = isinstance(rule, ClosingRule)
        if self.isclosure:
            self.closenodes = list(
                dict(n)
                for n in reversed(deque(rule.example_nodes())))
        else:
            self.closenodes = []
        self.istrunk = False

    def listen_on(self):
        super().listen_on()
        self.rule.tableau.on({
            Tableau.Events.BEFORE_TRUNK_BUILD : self.before_trunk_build,
            Tableau.Events.AFTER_TRUNK_BUILD  : self.after_trunk_build,
            Tableau.Events.AFTER_BRANCH_ADD   : self.after_branch_add,
            Tableau.Events.AFTER_NODE_ADD     : self.after_node_add})
        self.rule.on(Rule.Events.BEFORE_APPLY, self.before_apply)

    def before_trunk_build(self, *_):
        self.istrunk = True

    def after_trunk_build(self, *_):
        self.istrunk = False

    def after_branch_add(self, branch: Branch):
        if self.applied:
            return
        if len(self.closenodes) == 1:
            self.add_node(branch)        

    def after_node_add(self, node: Node, branch: Branch):
        if self.applied:
            return
        if node.meets(self.mynode) or isinstance(node, ClosureNode):
            return
        if self.istrunk:
            self.add_node(branch)
        elif self.closenodes and node.meets(self.closenodes[-1]):
            self.closenodes.pop()
            if len(self.closenodes) == 1:
                self.add_node(branch)

    def before_apply(self, target: Target):
        if self.applied:
            return
        if self.isclosure:
            return
        self.add_node(target.branch)

    def add_node(self, branch: Branch):
        self.applied.add(branch)
        branch.append(self.mynode)

# def rsttable(data, /, headers = (), **kw):
#     from tabulate import tabulate
#     return tabulate(data, headers, tablefmt = 'rst', **kw)

# def rawblock(content: list[str]|str, indent: str|int = None) -> list[str]:
#     'Make a raw html block from the lines. Returns a new list of lines.'
#     if isinstance(content, str):
#         content = content.splitlines()
#     lines = ['.. raw:: html', '', *indented(content, 4), '']
#     return indented(lines, indent)

# def indented(lines: Iterable[str], indent: str|int = None) -> list[str]:
#     'Indent non-empty lines. Indent can be string or number of spaces.'
#     if indent is None:
#         indent = ''
#     elif isinstance(indent, int):
#         indent *= ' '
#     return [
#         indent + line if len(line) else line
#         for line in lines
#     ]


