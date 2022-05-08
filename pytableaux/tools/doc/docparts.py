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
from functools import wraps

import html
import reprlib
import sys
from importlib import import_module
from typing import TYPE_CHECKING, Any, Callable, Sequence

from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import LexType, Operator
from pytableaux.lang.parsing import ParseTable
from pytableaux.lang.writing import LexWriter, RenderSet
from pytableaux.logics import registry
from pytableaux.proof.helpers import EllipsisExampleHelper
from pytableaux.proof.rules import ClosingRule, Rule
from pytableaux.proof.tableaux import Tableau
from pytableaux.tools import MapProxy, closure
from pytableaux.tools.hybrids import qset

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = (
    'lex_eg_table',
    'member_table',
    'opers_table',
    'rule_example_tableau',
    'Reprer',
    'Tabler',
    'trunk_example_tableau',
)

class Reprer(reprlib.Repr):

    defaults = MapProxy({
        'rstrole': 'obj',
    })

    attropts = {
        'maxlevel', 'maxtuple', 'maxlist', 'maxarray', 'maxdict', 'maxset',
        'maxfrozenset', 'maxdeque', 'maxstring', 'maxlong', 'maxother',
    }

    def __init__(self, **opts):
        super().__init__()
        self.opts = self.defaults | opts
        for key, value in self.opts.items():
            if key in self.attropts:
                setattr(self, key, value)

    def repr_rst_ref(self, obj, level):
        return self._fmt_rstrole(obj.__name__)

    repr_LangCommonEnumMeta = repr_LexicalAbcMeta = repr_rst_ref

    def _fmt_rstrole(self, text, /, role = None):
        if role is None:
            role = self.opts['rstrole']
        return f':{role}:`{text}`'

def fmt_raw(obj: Any):
    "No formatting."
    return obj

def fmt_literal(s: str):
    "Wrap in double backticks."
    return f'``{s}``'

def rule_example_tableau(rulecls: type[Rule], /, **opts) -> Tableau:
    "Get a rule's example tableau for documentation."
    tab = Tableau(registry.locate(rulecls), **opts)
    rule = tab.rules.get(rulecls)
    if isinstance(rule, ClosingRule): # TODO: fix for closure rules
        pass
    else:
        rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
    b = tab.branch().extend(rule.example_nodes())
    rule.apply(rule.target(b))
    return tab.finish()

def trunk_example_tableau(logic: Any, arg: Argument, /) -> str:
    "Get an example tableau for a logic's build_trunk for documentation."
    tab = Tableau(registry.locate(logic))
    # Pluck a rule.
    rule = tab.rules.groups[1][0]
    # Inject the helper.
    rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
    # Build trunk.
    tab.argument = arg
    return tab.finish()


@closure
def opers_table():

    # Source tables
    sources = (
        ParseTable.fetch('polish'),
        ParseTable.fetch('standard'),
        RenderSet.fetch('standard', 'unicode'),
        RenderSet.fetch('standard', 'html'),
    )

    def sources_info():
        for src in sources:
            if type(src) is ParseTable:
                yield (src.notation, 'ascii', True)
            else:
                yield (src.notation, src.charset, False)

    def src_func(o):
        # Get the operator symbols for the tables.
        for src in sources:
            if type(src) is ParseTable:
                func = src.char
            else:
                func = src.string
            yield func(o.TYPE, o)

    formats = [
        fmt_literal,
        fmt_literal,
        fmt_raw,
        lambda s: f'{html.unescape(s)} / {html.escape(s)}',
    ]

    def datarow(o) -> list[str]:
        return [
            fmt(value) for fmt, value in
            zip(formats, src_func(o))
        ]

    def build():
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

        # header info / columns
        head_cols = [
            blank[0:3],

            [ 'Notation',             'Charset', 'Can parse',   ], *(

            [ notn.name.capitalize(),  charset,  'NY'[canparse] ]

                for (notn, charset, canparse) in sources_info()
            )
        ]
        heads = list(zip(*head_cols))

        # Middle transition
        middle = [
            blank,
            ['Operator', *blank[:-1] ],
            blank,
        ]

        # main body rows
        main = [ [o.label, ''] + datarow(o) for o in Operator ]

        # Assemble
        header = heads[0]
        body = heads[1:] + middle + main
        return Tabler(body, header)

    return build


def lex_eg_table(columns: list[str], /, *,
    notn = 'standard', charset = 'unicode', maxtuple = 8):
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

    srepr = Reprer()
    srepr.maxtuple = maxtuple

    header = ['Type', 'Item', *columns]
    body = [
        [item.TYPE.name, lw(item),
            *map(srepr.repr, (getattr(item, name) for name in columns))
        ]
        for item in [
            m.cls.first() for m in LexType
        ]
    ]
    return Tabler(body, header)

# ------------------------------------------------

def member_table(owner: Sequence, columns: list[str], /, *, getitem = False):

    srepr = Reprer()

    if getitem:
        def getter(m, name):
            return m[name]
    else:
        getter = getattr
    header = columns
    body = [
        [getter(m, name) for name in columns]
        for m in owner
    ]

    table = Tabler(body, header)
    table.repr_apply(srepr.repr)
    return table

# ------------------------------------------------

class Tabler(list[list[str]]):
    header: list[str]
    body: list[list[str]]
    meta: dict[str, Any]
    __slots__ = 'header', 'body', 'meta'

    def __init__(self, body: list[list[str]], header: list[str]|None, /, **meta):
        self.header = header
        self.body = body
        self.meta = meta
        self.append(header)
        self.extend(body)

    def repr_apply(self, reprfunc: Callable, /):
        for row in self:
            for i, v in enumerate(row):
                if not isinstance(v, str):
                    row[i] = reprfunc(v)

    def tb(self, tablefmt = None, *, rp = None, **kw):
        from tabulate import tabulate as tb
        if rp:
            self.repr_apply(rp)
        return tb(self.body, self.header, tablefmt, **kw)

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

    class MemberTable(DirectiveHelper):

        required_arguments = 0
        optional_arguments = sys.maxsize

        def run(self):
            return member_table(
                self.current_class(),
                self.arguments
            )
            # self.env.ref_context['py:module']
            # args = self.arguments
            # if isinstance(args[0], str):
            #     args[0] = import_module(args[0])

            # return member_table(*self.args)

    directives.CSVTable.generators.update({
        'lex-eg-table'   : LexEgTable,
        'oper-sym-table' : OperSymTable,
        'member-table'   : MemberTable,
    })

# ------------------------------------------------

def _randgen(src):
    from random import shuffle
    src = list(src)
    shuffle(src)
    while True:
        yield from src

def prargs(*args):
    for arg in args:
        print(arg)

def main():
    "Terminal main. Print rando tables."

    from random import shuffle

    import tabulate as Tb
    from pytableaux.lang import LexType, Operator
    from tabulate import tabulate as tb
    from typing import Iterator

    theformats = qset(Tb.tabulate_formats)
    theformats -= {f for f in theformats if
        'latex' in f or 'html' in f
    }
    prargs('', theformats, '', '',)
    fmtit = _randgen(theformats)
   
    lexatrs = ['spec', 'ident', 'sort_tuple']
    shuffle(lexatrs)

    def callspec_it() -> Iterator[
        tuple[Callable[..., Tabler], Any,]
    ]:
        callspecs = [
            (opers_table,),

            (lex_eg_table, lexatrs[0:2]),

            *((lex_eg_table, [name]) for name in lexatrs),

            (member_table, Operator, [
                'name','order', 'label', 'arity', 'libname']),

            (member_table, LexType, [
                'name', 'rank', 'cls', 'role', 'maxi'])
        ]

        shuffle(callspecs)
        return iter(callspecs)


    for func, *args in callspec_it():

        tablefmt = next(fmtit)
        inforow = [func.__name__, tablefmt]
        info = tb([ inforow ], tablefmt = 'fancy_outline')

        table = func(*args)
        prargs(
            info, '', '',
            table.tb(tablefmt), '', '',
        )


if __name__ == '__main__':
    main()
