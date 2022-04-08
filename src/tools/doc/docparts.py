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
#
# ------------------
#
# pytableaux - misc doc elements
from __future__ import annotations

__all__ = (
    'opers_table',
    'rule_example_tableau',
    'trunk_example_tableau',
)

from lexicals import Argument, Operator, RenderSet
from parsers import ParseTable
from proof.helpers import EllipsisExampleHelper
from proof.tableaux import ClosingRule, Rule, Tableau
from tools.misc import get_logic
from html import unescape as html_unescape
from typing import Any

def rule_example_tableau(rule: Rule|type[Rule]|str, /, logic: Any = None, **opts) -> Tableau:
    "Get a rule's example tableau for documentation."
    logic = get_logic(logic or rule)
    tab = Tableau(logic, **opts)
    rule = tab.rules.get(rule)
    if isinstance(rule, ClosingRule):
        # TODO: fix for closure rules
        pass
    else:
        rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
    b = tab.branch()
    b.extend(rule.example_nodes())
    rule.apply(rule.target(b))
    tab.finish()
    return tab

def trunk_example_tableau(logic: Any, arg: Argument, /) -> str:
    "Get an example tableau for a logic's build_trunk for documentation."
    logic = get_logic(logic)
    tab = Tableau(logic)
    # Pluck a rule.
    rule = tab.rules.groups[1][0]
    # Inject the helper.
    rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
    # Build trunk.
    tab.argument = arg
    tab.finish()
    return tab

def opers_table() -> list[list[str]]:
    'Table data for the Operators table.'
    charpol, charstd = (
        {o: table.char(o.TYPE, o) for o in Operator}
        for table in (
            ParseTable.fetch('polish'),
            ParseTable.fetch('standard'),
        )
    )
    strhtml, strunic = (
        {o: rset.string(o.TYPE, o) for o in Operator}
        for rset in (
            RenderSet.fetch('standard', 'html'),
            RenderSet.fetch('standard', 'unicode'),
        )
    )
    pre = '``{}``'.format
    heads = (
        ['', '', '', 'Render only'],
        ['Operator', 'Polish', 'Standard', 'Std. HTML', 'Std. Unicode'],
    )
    body = [
        [o.label, pre(charpol[o]), pre(charstd[o]), html_unescape(strhtml[o]), strunic[o]]
        for o in Operator
    ]
    rows = list(heads)
    rows.extend(body)
    return rows