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
import sys
from functools import partial
from types import MappingProxyType as MapProxy
from typing import Any, Callable, Sequence

from sphinx.application import Sphinx

from ...lang import LexType, LexWriter, Operator, ParseTable, RenderSet
from .. import abcs, closure, qset
from . import ConfKey, Tabler, directives
from .directives import TableGenerator

__all__ = (
    'lex_eg_table',
    'member_table',
    'oper_sym_table',
    'Reprer')

def fmt_raw(obj: Any):
    "No formatting."
    return obj

def fmt_literal(s: str):
    "Wrap in double backticks."
    return f'``{s}``'

def fmt_ref(obj: Any, role = None):
    if role is None:
        role = 'obj'
    if isinstance(obj, type):
        role = 'class'
        text = obj.__name__
    else:
        text = str(obj)
    return f':{role}:`{text}`'


class Reprer(reprlib.Repr, dict, metaclass = abcs.AbcMeta):

    defaults = MapProxy(dict(

        maxlevel =     6 * 2,
        maxtuple =     6 * 4,
        maxlist  =     6 * 4,
        maxarray =     5 * 4,
        maxdict  =     4 * 4,
        maxset   =     6 * 4,
        maxfrozenset = 6 * 4,
        maxdeque =     6 * 4,
        maxstring =   30 * 2,
        maxlong   =   40 * 2,
        maxother  =   30 * 2,

        lw = repr))

    attropts = set(defaults)

    lw: Callable

    def __init__(self, **opts):
        self.instmap = {}
        self.instconds = self.instmap.items()
        self.opts = self.defaults | opts
        for key, value in self.opts.items():
            if key in self.attropts:
                setattr(self, key, value)

    __call__ = reprlib.Repr.repr

    def repr1(self, x, level):
        try:
            f = self[type(x)]
        except KeyError:
            for info, f in self.instconds:
                if isinstance(x, info):
                    return f(x)
        else:
            return f(x)
        return super().repr1(x, level)

    def repr_lexclass(self, obj, level):
        return fmt_ref(obj, role = 'cls')

    def repr_lexical(self, obj, level):
        return self.lw(obj)

    @abcs.abcf.after
    def _(cls):
        fmc = 'repr_{0.__name__}'.format
        for m in LexType:
            setattr(cls, fmc(type(m.cls)), cls.repr_lexclass)
            setattr(cls, fmc(m.cls), cls.repr_lexical)

# ------------------------------------------------
# ------------------------------------------------

@closure
def oper_sym_table():

    # Source tables
    sources = (
        ParseTable.fetch('polish'),
        ParseTable.fetch('standard'),
        RenderSet.fetch('standard', 'unicode'),
        RenderSet.fetch('standard', 'html'))

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
        fmt_raw,#lambda s: f'{html.unescape(s)} / {html.escape(s)}',
    ]

    def datarow(o) -> list[str]:
        return [
            fmt(value) for fmt, value in
            zip(formats, src_func(o))]

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

        # main body rows
        main = [ [o.label, ''] + datarow(o) for o in Operator ]

        # Assemble
        header = heads[0]
        body = heads[1:] + middle + main
        return Tabler(body, header)

    return build

class OperSymTable(TableGenerator):

    def gentable(self):
        return oper_sym_table()

directives.table_generators['oper-sym-table'] = OperSymTable

# ------------------------------------------------
# ------------------------------------------------

def lex_eg_table(columns: list[str], /, *, 
    notn = 'standard', charset = 'unicode',):
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
    reprer = Reprer(lw = LexWriter(notn, charset))

    header = ['Type', 'Item', *columns]
    data = [
        [type(item), item, *map(partial(getattr, item), columns)]
        for item in (m.cls.first() for m in LexType)
    ]

    return Tabler(data, header).apply_repr(reprer)

class LexEgTable(TableGenerator):

    required_arguments = 1
    optional_arguments = sys.maxsize

    def gentable(self):
        conf = self.config
        kwargs = dict(
            notn = conf[ConfKey.wnotn]
        )
        return lex_eg_table(self.arguments, **kwargs)

directives.table_generators['lex-eg-table'] = LexEgTable

# ------------------------------------------------
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
        for m in owner]

    return Tabler(body, header).apply_repr(srepr)

class MemberTable(TableGenerator):

    required_arguments = 0
    optional_arguments = sys.maxsize

    def gentable(self):
        return member_table(self.current_class(), self.arguments)

directives.table_generators['member-table'] = MemberTable

# ------------------------------------------------

def setup(app: Sphinx):
    "Sphinx setup."
    pass

# ------------------------------------------------

def _randgen(src):
    from random import shuffle
    src = list(src)
    shuffle(src)
    while True:
        yield from src

def prblock(*args):
    for arg in args:
        print(arg)
    print('\n')

def main():
    "Terminal main. Print rando tables."

    from random import shuffle
    from typing import Iterator

    import tabulate as Tb
    from tabulate import tabulate as tb

    from pytableaux.lang import LexType, Operator

    theformats = qset(Tb.tabulate_formats)
    theformats -= {f for f in theformats if
        'latex' in f or 'html' in f}
    prblock('Formats:', theformats)
    fmtit = _randgen(theformats)
   
    lexatrs = ['spec', 'ident', 'sort_tuple']
    shuffle(lexatrs)

    def callspec_it() -> Iterator[tuple[Callable[..., Tabler], Any]]:
        callspecs = [
            (oper_sym_table,),
            (lex_eg_table, lexatrs[0:2]),
            *((lex_eg_table, [name]) for name in lexatrs),
            (member_table, Operator, [
                'name','order', 'label', 'arity', 'libname']),
            (member_table, LexType, [
                'name', 'rank', 'cls', 'role', 'maxi'])]
        shuffle(callspecs)
        return iter(callspecs)

    for func, *args in callspec_it():

        table = func(*args)
        tablefmt = next(fmtit)

        prblock(tb(
            [
                [func.__name__, tablefmt, ', '.join(map(repr,args))]
            ],
            ['function', 'format', 'args'],
            tablefmt = 'fancy_outline'
        ))

        prblock(
            # print(csvlines(table)), '', '',
            table.tb(tablefmt), #'', '',
        )


if __name__ == '__main__':
    main()
