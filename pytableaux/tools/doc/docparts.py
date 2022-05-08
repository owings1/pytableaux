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

import html
import reprlib
import sys
from typing import TYPE_CHECKING, Any

from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import LexType, Operator
from pytableaux.lang.parsing import ParseTable
from pytableaux.lang.writing import LexWriter, RenderSet
from pytableaux.logics import registry
from pytableaux.proof.helpers import EllipsisExampleHelper
from pytableaux.proof.rules import ClosingRule, Rule
from pytableaux.proof.tableaux import Tableau
from pytableaux.tools import closure

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = (
    'lex_eg_table',
    'opers_table',
    'rule_example_tableau',
    'trunk_example_tableau',
)

class SpecRepr(reprlib.Repr):

    def repr_TriCoords(self, obj, level):
        return self.repr(tuple(obj))
    repr_BiCoords = repr_TriCoords

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

def fmt_raw(obj: Any):
    "No formatting."
    return obj

def fmt_literal(s: str):
    "Wrap in double backticks."
    return f'``{s}``'


@closure
def opers_table():

    def oper_data(o):
        # Get the operator symbols.
        for src in sources:
            if type(src) is ParseTable:
                func = src.char
            else:
                func = src.string
            yield func(o.TYPE, o)

    def sources_info():
        for src in sources:
            if type(src) is ParseTable:
                yield (src.notation, 'ascii', True)
            else:
                yield (src.notation, src.charset, False)

    sources = (
        ParseTable.fetch('polish'),
        ParseTable.fetch('standard'),
        RenderSet.fetch('standard', 'unicode'),
        RenderSet.fetch('standard', 'html'),
    )

    formats = [
        fmt_literal,
        fmt_literal,
        fmt_raw,
        lambda s: f'{html.unescape(s)} / {html.escape(s)}',
    ]

    def build(*, flat = True):
        """Table data for the Operators symbols table.

        Example:

        ======================  =========  ======  ========  ========  ===============
        ..                      Notation   Polish  Standard  Standard  Standard
        ..                      Charset    ascii   ascii     unicode   html
        ..                      Can parse  Y       Y         N         N
        ..
        Operator
        ..
        Assertion                          ``T``   ``*``     ○         ○ / &amp;#9675;
        Negation                           ``N``   ``~``     ¬         ¬ / &amp;not;
        Conjunction                        ``K``   ``&``     ∧         ∧ / &amp;and;
        Disjunction                        ``A``   ``V``     ∨         ∨ / &amp;or;
        Material Conditional               ``C``   ``>``     ⊃         ⊃ / &amp;sup;
        Material Biconditional             ``E``   ``<``     ≡         ≡ / &amp;equiv;
        Conditional                        ``U``   ``$``     →         → / &amp;rarr;
        Biconditional                      ``B``   ``%``     ↔         ↔ / &amp;harr;
        Possibility                        ``M``   ``P``     ◇         ◇ / &amp;#9671;
        Necessity                          ``L``   ``N``     ◻         ◻ / &amp;#9723;
        ======================  =========  ======  ========  ========  ===============
        """

        width = 2 + len(sources)
        blank = [''] * width

        # main body rows
        main = [
            [o.label, '', *(fmt(value) for fmt, value in zip(
                formats, oper_data(o)))
            ]
            for o in Operator
        ]
        # header info / columns
        head_cols = [
            blank[0:3],
            [
                'Notation',
                'Charset',
                'Can parse',
            ], *(
                [
                    notn.name.capitalize(),
                    charset,
                    'NY'[canparse]
                ]
                for (notn, charset, canparse)
                in sources_info()
            )
        ]
        heads = list(zip(*head_cols))
        # Middle transition
        middle = [
            blank,
            ['Operator', *blank[:-1] ],
            blank,
        ]
        # Assemble
        header = heads[0]
        body = heads[1:] + middle + main
        if flat:
            return [header] + body
        return body, header

    return build


def lex_eg_table(columns: list[str], /, *,
    notn = 'standard', charset = 'unicode',
    flat = False):
    "lexical item attribute examples."
    """
    Example:

    ╒════════════╤════════╤════════════════════════════════════╕
    │ Type       │ Item   │ sort_tuple                         │
    ╞════════════╪════════╪════════════════════════════════════╡
    │ Predicate  │ F      │ (10, 0, 0, 1)                      │
    │ Constant   │ a      │ (20, 0, 0)                         │
    │ Variable   │ x      │ (30, 0, 0)                         │
    │ Quantifier │ ∃      │ (40, 0)                            │
    │ Operator   │ ○      │ (50, 10)                           │
    │ Atomic     │ A      │ (60, 0, 0)                         │
    │ Predicated │ Fa     │ (70, 10, 0, 0, 1, 20, 0, 0)        │
    │ Quantified │ ∃xFx   │ (80, 40, 0, 30, 0, 0, 70, 10, ...) │
    │ Operated   │ ○A     │ (90, 50, 10, 60, 0, 0)             │
    ╘════════════╧════════╧════════════════════════════════════╛
    """
    lw = LexWriter(notn, charset)

    srepr = SpecRepr()
    srepr.maxtuple = 8

    header = ['Type', 'Item', *columns]
    body = [
        [
            item.TYPE.name,
            lw(item),
            *map(srepr.repr, (
                getattr(item, name)
                for name in columns)
            )
        ]
        for item in [
            m.cls.first() for m in LexType
        ]
    ]
    if flat:
        return [header] + body
    return body, header

# ------------------------------------------------

def setup(app: Sphinx):
    "Sphinx setup."

    from pytableaux.tools.doc import DirectiveHelper, directives

    class OperSymTable(DirectiveHelper):
        run = staticmethod(opers_table)

    class LexEgTable(DirectiveHelper):
        required_arguments = 1
        optional_arguments = sys.maxsize
        def run(self):
            return lex_eg_table(self.arguments)

    directives.CSVTable.generators.update({
        'lex-eg-table'   : LexEgTable,
        'oper-sym-table' : OperSymTable,
    })

# ------------------------------------------------

def main():
    "Terminal main. Print rando tables."

    import tabulate as Tb
    from tabulate import tabulate as tb
    from random import shuffle

    flat = False

    def _randgen():
        formats = list(Tb.tabulate_formats)
        while True:
            shuffle(formats)
            yield from formats
    fmtit = _randgen()
    del(_randgen)

    lexatrs = ['spec', 'ident', 'sort_tuple']
    shuffle(lexatrs)

    def callspec_it():
        callspecs = [
            (opers_table,),
            (lex_eg_table, lexatrs[0:2]),
            *((lex_eg_table, [name]) for name in lexatrs),
        ]
        shuffle(callspecs)
        return iter(callspecs)

    def prargs(*args):
        for arg in args:
            print(arg)

    def pr(body, headers = [], tablefmt = None, *args, func = None, **kw):

        if tablefmt is None:
            tablefmt = next(fmtit)
        inforow = []
        infohead = []

        if func is None:
            inforow.append('?')
        else:
            inforow.append(func.__name__)
        inforow.append(tablefmt)

        info = tb([ inforow ], infohead, tablefmt = 'fancy_outline')

        prargs(
            info,
            '\n',
            tb(body, headers, tablefmt, *args, **kw),
            '\n'
        )

    for func, *args in callspec_it():
        rows = func(*args, flat = flat)
        if flat:
            header = []
        else:
            rows, header = rows
        pr(rows, header, tablefmt = next(fmtit), func = func)


if __name__ == '__main__':
    main()