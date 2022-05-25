# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
pytableaux.tools.doc.rstutils
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations
from collections import defaultdict

import re
from inspect import getsource
from typing import TYPE_CHECKING
import enum
from pytableaux import logics
from pytableaux.lang import Operator, Quantifier, Predicate
from pytableaux.logics import LogicLocatorRef, registry
from pytableaux.proof import TableauxSystem as TabSys
from pytableaux.proof import ClosingRule, Rule, helpers, Branch
from pytableaux.proof.util import RuleEvent, TabEvent, NodeAttr
from pytableaux.tools import abcs
from pytableaux.tools.abcs import isabstract
from sphinx.ext.autodoc.importer import import_object

if TYPE_CHECKING:
    from pytableaux.proof import Node, Rule, Target
    from pytableaux.tools.typing import LogicType
    from typing import Any, overload, Collection

__all__ = (
    'EllipsisExampleHelper',
    'get_logic_names',
    'is_concrete_build_trunk',
    'is_concrete_rule',
    'is_transparent_rule',
)

# def get_logic_names(logic_docdir: str = None, suffix: str = '.rst', /) -> set[str]:
#     'Get all logic names with a .rst document in the doc dir.'
#     if logic_docdir is None:
#         logic_docdir = os.path.abspath(
#             os.path.join(os.path.dirname(__file__), '../../../doc/logics')
#         )
#     return set(
#         os.path.basename(file).removesuffix(suffix).upper()
#         for file in os.listdir(logic_docdir)
#         if file.endswith(suffix)
#     )

def is_concrete_rule(obj: Any, /) -> bool:
    return _is_rulecls(obj) and obj not in (Rule, ClosingRule)

def is_concrete_build_trunk(obj: Any, /,):
    return TabSys.build_trunk in _methmro(obj) and not isabstract(obj)
    # return obj is not TabSys.build_trunk and TabSys.build_trunk in _methmro(obj)

def is_transparent_rule(obj: Any) -> bool:
    """Whether a rule class:
        - is included in TabRules groups for the module it belongs to
        - inherits from a rule class that belongs to another logic module
        - the parent class is in the other logic's rule goups
        - there is no implementation besides pass
        - there is no docblock
    """
    return (
        _is_rulecls(obj) and
        _is_nodoc(obj) and
        _is_nocode(obj) and
        _rule_is_self_grouped(obj) and
        _rule_is_parent_grouped(obj)
    )


def rule_legend(rule: type[Rule]|Rule):

    if isinstance(rule, Rule):
        rule = type(rule)

    legend = {}

    if getattr(rule, 'negated', None):
        legend['negated'] = Operator.Negation

    if (oper := getattr(rule, 'operator', None)):
        legend['operator'] = Operator[oper]
    elif (quan := getattr(rule, 'quantifier', None)):
        legend['quantifier'] = Quantifier[quan]
    elif (pred := getattr(rule, 'predicate', None)):
        legend['predicate'] = Predicate(pred)

    if (des := getattr(rule, 'designation', None)) is not None:
        legend['designation'] = des

    if (issubclass(rule, ClosingRule)):
        legend['closure'] = True

    return tuple(legend.items())


def rules_sorted(logic: LogicType, rules: Collection[type[Rule]] = None, /) -> dict[str, list[type[Rule]]]:

    logic = logics.registry(logic)
    RulesCls = logic.TabRules
    if rules is None:
        rules = list(RulesCls.all_rules)
    results = {}

    results['member_order'] = rules_sorted_member_order(logic, rules)
    # results['legend_order'] = sorted(rules, key = LegendSortFlag.rulekey)
    results['legend_order'] = rules_sorted_legend_order(rules)
    from pprint import pp
    # pp(inherit_map)
    # pp(keys_member_order)
    return results
    # return native_members

def rules_sorted_legend_order(rules: Collection[type[Rule]], /) -> list[type[Rule]]:
    groups = {name: [] for name in ('closure', 'operator', 'quantifier', 'predicate')}
    ungrouped = []
    legends: dict[type[Rule], dict] = {}
    for rule in rules:
        legends[rule] = legend = dict(rule_legend(rule))
        for name in legend:
            if name in groups:
                groups[name].append(rule)
                break
        else:
            ungrouped.append(rule)
    for name, group in groups.items():
        group.sort(key = lambda rule: (
            (1 * bool(legends[rule].get('negated'))) + 
            (2 * legends[rule].get('designated', 0))
        ))
        group.sort(key = lambda rule: legends[rule][name])
    groups['ungrouped'] = ungrouped
    return list(rule for group in groups.values() for rule in group)

def rules_sorted_member_order(logic: LogicType, rules: Collection[type[Rule]], /) -> list[type[Rule]]:
    RulesCls = logic.TabRules
    native_members = []
    todo = set(rules)
    for member in RulesCls.__dict__.values():
        if member in todo:
            native_members.append(member)
            todo.remove(member)
    keys_member_order = {rule: i for i, rule in enumerate(native_members, 1)}
    inherit_map = defaultdict(set)
    for rule in todo:
        inherit_map[logics.registry.locate(rule)].add(rule)
    for parent, values in inherit_map.items():
        others = inherit_map[parent] = rules_sorted_member_order(parent, values)
        keys_member_order.update({
            rule: i for i, rule in enumerate(others, len(keys_member_order))
        })
    return sorted(rules, key = keys_member_order.__getitem__)
# ------------------------------------------------

if TYPE_CHECKING:

    @overload
    def is_enum_member(modname: str, objpath: list[str]):
        "Prefered method if info is available."

    @overload
    def is_enum_member(fullname: str):
        "Fallback method that tries to guess module path."

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


def _is_rulecls(obj: Any) -> bool:
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

def _rule_is_grouped(rule: type[Rule], logic: LogicLocatorRef) -> bool:
    'Whether the rule class is grouped in the TabRules of the given logic.'
    if not _is_rulecls(rule):
        return False
    try:
        logic = registry.locate(logic)
    except:
        return False
    tabrules = logic.TabRules
    if rule in tabrules.closure_rules:
        return True
    for grp in tabrules.rule_groups:
        if rule in grp:
            return True
    return False

def _rule_is_self_grouped(rule: type[Rule]) -> bool:
    'Whether the Rule class is grouped in the TabRules of its own logic.'
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

class EllipsisExampleHelper:

    mynode = {'ellipsis': True}
    closenodes: list[Node]
    applied: set[Branch]
    isclosure: bool
    istrunk: bool

    def __init__(self, rule: Rule,/):
        self.rule = rule
        self.applied = set()
        self.closenodes = []
        
        self.isclosure = isinstance(rule, ClosingRule)
        if self.isclosure:
            self.closenodes = list(
                dict(n)
                for n in reversed(rule.example_nodes())
            )
        self.istrunk = False
        rule.tableau.on({
            TabEvent.BEFORE_TRUNK_BUILD : self.before_trunk_build,
            TabEvent.AFTER_TRUNK_BUILD  : self.after_trunk_build,
            TabEvent.AFTER_BRANCH_ADD   : self.after_branch_add,
            TabEvent.AFTER_NODE_ADD     : self.after_node_add,
        })
        rule.on(RuleEvent.BEFORE_APPLY, self.before_apply)

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
        if node.meets(self.mynode) or node.is_closure:
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
        branch.add(self.mynode)

    



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


