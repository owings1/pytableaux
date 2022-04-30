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
pytableaux.tools.doc.docparts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import reprlib
from typing import Any

from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import Lexical, LexType, Operator
from pytableaux.lang.parsing import ParseTable
from pytableaux.lang.writing import LexWriter, RenderSet
from pytableaux.logics import registry
from pytableaux.proof.helpers import EllipsisExampleHelper
from pytableaux.proof.rules import ClosingRule, Rule
from pytableaux.proof.tableaux import Tableau

__all__ = (
    'opers_table',
    'rule_example_tableau',
    'trunk_example_tableau',
)

def rule_example_tableau(rulecls: type[Rule], /, **opts) -> Tableau:
    "Get a rule's example tableau for documentation."
    logic = registry.locate(rulecls)
    tab = Tableau(logic, **opts)
    rule = tab.rules.get(rulecls)
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
    logic = registry.locate(logic)
    tab = Tableau(logic)
    # Pluck a rule.
    rule = tab.rules.groups[1][0]
    # Inject the helper.
    rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
    # Build trunk.
    tab.argument = arg
    tab.finish()
    return tab

pre = '``{}``'.format

TableData = list[list[str]]

def opers_table(opts: dict = {}) -> TableData:
    'Table data for the Operators table.'

    from html import escape, unescape

    # Build outputs into maps
    # Parser tables
    charpol, charstd = (
        {o: table.char(o.TYPE, o) for o in Operator}
        for table in (
            ParseTable.fetch('polish'),
            ParseTable.fetch('standard'),
        )
    )
    # Render tables
    strhtml, strunic = (
        {o: rset.string(o.TYPE, o) for o in Operator}
        for rset in (
            RenderSet.fetch('standard', 'html'),
            RenderSet.fetch('standard', 'unicode'),
        )
    )

    # ordered symbol lookups
    #        0            1           2            3
    #      polish.ascii  std.ascii, std.unicode, std.html
    maps = [charpol,     charstd,    strunic,      strhtml]
    # raw symbol table outputs
    rawrows = [
        [m[o] for m in maps]
        for o in Operator
    ]
    # formatted symbol cells
    symbolrows = [
        [
            pre(r[0]),
            pre(r[1]),
            r[2],
            f'{unescape(r[3])} / {escape(r[3])}'
        ]
        for r in rawrows
    ]
    
    heads = [

        ['', 'Notation',   'Polish', 'Standard',   'Standard',   'Standard'],
        ['', 'Charset',    'ascii',  'ascii'  ,    'unicode'   ,   'html' ],
        ['', 'Can parse',      'Y',    'Y',          'N'      ,     'M'     ],

    ]
    cols = len(heads[0])

    operrow = ['Operator'] + [''] * (cols - 1)


    # table layour
    body = [
        [o.label ,'' , r[0], r[1], r[2], r[3]]

        for o, r in zip(
            Operator, symbolrows
        )
    ]

    spacerrow = [''] * cols

    rows = list(heads)

    rows.append(spacerrow)
    rows.append(operrow)
    rows.append(spacerrow)

    rows.extend(body)

    return rows

class SpecRepr(reprlib.Repr):

    def repr_TriCoords(self, obj, level):
        return self.repr(tuple(obj))
    repr_BiCoords = repr_TriCoords


def lex_eg_table(choice = 'spec', opts: dict = {}) -> TableData:

    def egitem(lexcls: type[Lexical]):
        return lexcls.first()

    egitems = [egitem(lexcls) for lexcls in LexType.classes]
    lw = LexWriter('standard', 'unicode')

    srepr = SpecRepr().repr

    # header row data
    hdata = dict(
        spec        = 'spec',
        ident       = 'ident',
        sort_tuple  = 'sort_tuple',
        hash        = 'hash'
    )
    # row data for python repr
    rdata = [
        [item, type(item),
        dict(
            spec       = srepr(item.spec),
            ident      = srepr(item.ident),
            sort_tuple = srepr(item.sort_tuple),
            hash       = srepr(item.hash)
        )]
        for item in egitems
    ]

    
    # table with one 'attribute' column
    heads = [
        # one header row
        ['Type', 'Item', hdata[choice]]
    ]
    body = [
        [lexcls.__name__, lw(item), row[choice]]
        for item, lexcls, row in rdata
    ]

    rows = list(heads)
    rows.extend(body)

    return rows
