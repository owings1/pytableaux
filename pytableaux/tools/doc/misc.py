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

from typing import TYPE_CHECKING

from pytableaux.proof import ClosingRule
from pytableaux.proof.util import RuleEvent, TabEvent

if TYPE_CHECKING:
    from pytableaux.proof import Branch, Node, Rule, Target

__all__ = (
    'EllipsisExampleHelper',
)

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


