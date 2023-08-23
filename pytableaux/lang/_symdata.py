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
pytableaux.lang._symdata
^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import re
from types import MappingProxyType as MapProxy
from typing import Any, Callable, Mapping

from ..tools import closure

__all__ = ()

def parsetables():
    from . import Marking, Notation
    from .lex import LexType, Operator, Predicate, Quantifier

    data = {
        Notation.standard: dict(
            default = {
                'A' : (LexType.Atomic, 0),
                'B' : (LexType.Atomic, 1),
                'C' : (LexType.Atomic, 2),
                'D' : (LexType.Atomic, 3),
                'E' : (LexType.Atomic, 4),
                '*' : (LexType.Operator, Operator.Assertion),
                '~' : (LexType.Operator, Operator.Negation),
                '&' : (LexType.Operator, Operator.Conjunction),
                'V' : (LexType.Operator, Operator.Disjunction),
                '>' : (LexType.Operator, Operator.MaterialConditional),
                '<' : (LexType.Operator, Operator.MaterialBiconditional),
                '$' : (LexType.Operator, Operator.Conditional),
                '%' : (LexType.Operator, Operator.Biconditional),
                'P' : (LexType.Operator, Operator.Possibility),
                'N' : (LexType.Operator, Operator.Necessity),
                'x' : (LexType.Variable, 0),
                'y' : (LexType.Variable, 1),
                'z' : (LexType.Variable, 2),
                'v' : (LexType.Variable, 3),
                'a' : (LexType.Constant, 0),
                'b' : (LexType.Constant, 1),
                'c' : (LexType.Constant, 2),
                'd' : (LexType.Constant, 3),
                '=' : (Predicate.System, Predicate.System.Identity),
                '!' : (Predicate.System, Predicate.System.Existence),
                'F' : (LexType.Predicate, 0),
                'G' : (LexType.Predicate, 1),
                'H' : (LexType.Predicate, 2),
                'O' : (LexType.Predicate, 3),
                'L' : (LexType.Quantifier, Quantifier.Universal),
                'X' : (LexType.Quantifier, Quantifier.Existential),
                '(' : (Marking.paren_open, 0),
                ')' : (Marking.paren_close, 0),
                ' ' : (Marking.whitespace, 0),
                '0' : (Marking.digit, 0),
                '1' : (Marking.digit, 1),
                '2' : (Marking.digit, 2),
                '3' : (Marking.digit, 3),
                '4' : (Marking.digit, 4),
                '5' : (Marking.digit, 5),
                '6' : (Marking.digit, 6),
                '7' : (Marking.digit, 7),
                '8' : (Marking.digit, 8),
                '9' : (Marking.digit, 9),
            }
        ),
        Notation.polish: dict(
            default = {
                'a' : (LexType.Atomic, 0),
                'b' : (LexType.Atomic, 1),
                'c' : (LexType.Atomic, 2),
                'd' : (LexType.Atomic, 3),
                'e' : (LexType.Atomic, 4),
                'T' : (LexType.Operator, Operator.Assertion),
                'N' : (LexType.Operator, Operator.Negation),
                'K' : (LexType.Operator, Operator.Conjunction),
                'A' : (LexType.Operator, Operator.Disjunction),
                'C' : (LexType.Operator, Operator.MaterialConditional),
                'E' : (LexType.Operator, Operator.MaterialBiconditional),
                'U' : (LexType.Operator, Operator.Conditional),
                'B' : (LexType.Operator, Operator.Biconditional),
                'M' : (LexType.Operator, Operator.Possibility),
                'L' : (LexType.Operator, Operator.Necessity),
                'x' : (LexType.Variable, 0),
                'y' : (LexType.Variable, 1),
                'z' : (LexType.Variable, 2),
                'v' : (LexType.Variable, 3),
                'm' : (LexType.Constant, 0),
                'n' : (LexType.Constant, 1),
                'o' : (LexType.Constant, 2),
                's' : (LexType.Constant, 3),
                'I' : (Predicate.System, Predicate.System.Identity),
                'J' : (Predicate.System, Predicate.System.Existence),
                'F' : (LexType.Predicate, 0),
                'G' : (LexType.Predicate, 1),
                'H' : (LexType.Predicate, 2),
                'O' : (LexType.Predicate, 3),
                'V' : (LexType.Quantifier, Quantifier.Universal),
                'S' : (LexType.Quantifier, Quantifier.Existential),
                ' ' : (Marking.whitespace, 0),
                '0' : (Marking.digit, 0),
                '1' : (Marking.digit, 1),
                '2' : (Marking.digit, 2),
                '3' : (Marking.digit, 3),
                '4' : (Marking.digit, 4),
                '5' : (Marking.digit, 5),
                '6' : (Marking.digit, 6),
                '7' : (Marking.digit, 7),
                '8' : (Marking.digit, 8),
                '9' : (Marking.digit, 9),
            },
        ),
    }
    return data

def string_tables():

    from html import unescape as html_unescape

    from ..tools import dmerged
    from . import LexType, Marking, Notation, Operator, Predicate, Quantifier

    def dunesc(d: dict, inplace = False) -> None:
        return dtransform(html_unescape, d, typeinfo = str, inplace = inplace)


    subsym = MapProxy(dict(
        ascii = {
            Marking.subscript_open: '',
            Marking.subscript_close: '',
        },
        html = {
            Marking.subscript_open: '<sub>',
            Marking.subscript_close: '</sub>',
        },
        latex = {
            Marking.subscript_open: '_{',
            Marking.subscript_close: '}',
        },
        rst = {
            Marking.subscript_open: ':sub:`',
            Marking.subscript_close: '`',
        },
        unicode = {
            Marking.subscript_open: '.[',
            Marking.subscript_close: ']',
        }))
    # meta chars
    metachar = MapProxy(dict(
        ascii = MapProxy(dict(
            conseq    = '|-',
            nonconseq = '|/-',
            therefore = ':.',
            ellipsis  = '...')),
        html = MapProxy(dict(
            conseq    = '&vdash;',
            nonconseq = '&nvdash;',
            therefore = '&there4;',
            ellipsis  = '&hellip;')),
        latex = MapProxy(dict(
            conseq    = '\\Vdash',
            nonconseq = '\\nVdash',
            therefore = '\\therefore',
            ellipsis  = '\\ldots'))))
    
    # tab symbols
    tabsym = dict(
        ascii = {
            ('designation', True) :  '[+]',
            ('designation', False):  '[-]',
            ('flag', 'closure') : '(x)',
            ('flag', 'quit') : '(q)',
            ('access', 'symmetric') : 'R(sym)',
            ('access', 'transitive') : 'R(+)',
            ('access', 'reflexive'): 'R(<=)',
            ('access', 'serial'): 'R(ser)',
            'access': 'R'},
        html = {
            ('designation', True) : '&oplus;',  # '\2295'
            ('designation', False): '&ominus;', # '\2296'
            ('flag', 'closure') : '&otimes;', # '\2297'
            ('flag', 'quit'): '&#9872;', # '⚐', '\U+2690'
            ('access', 'symmetric'): 'R&#9007;', # '⌯', '\U+232F'
            ('access', 'transitive'): 'R+',
            ('access', 'reflexive'): 'R&le;',
            ('access', 'serial'): 'Rser',
            'access': 'R'},
        latex = {
            ('designation', True) : '\\varoplus{}',
            ('designation', False) : '\\varominus{}',
            ('flag', 'closure') : '\\varotimes{}',
            ('flag', 'quit') : '\\bowtie{}',
            ('access', 'symmetric') : '\\mathcal{R}_{sym}',
            ('access', 'transitive') : '\\mathcal{R}_{+}',
            ('access', 'reflexive') : '\\mathcal{R}_{\\leq{}}',
            ('access', 'serial') : '\\mathcal{R}_{ser}',
            'access': '\\mathcal{R}'})

    for key in tabsym:
        # (flag, closure) is for generic tab node writing
        # (closure, True) is for rule legend writing
        tabsym[key]['closure', True] = tabsym[key]['flag', 'closure']

    data = {notn: {} for notn in Notation}

    Notation.polish
    '---------------'

    # Start with html, and most things can be unescaped.

    data[Notation.polish]['html'] = prev = dict(
        notation = Notation.polish,
        format  = 'html',
        strings = {
            LexType.Atomic   : tuple('abcde'),
            LexType.Operator : {
                Operator.Assertion              : 'T',
                Operator.Negation               : 'N',
                Operator.Conjunction            : 'K',
                Operator.Disjunction            : 'A',
                Operator.MaterialConditional    : 'C',
                Operator.MaterialBiconditional  : 'E',
                Operator.Conditional            : 'U',
                Operator.Biconditional          : 'B',
                Operator.Possibility            : 'M',
                Operator.Necessity              : 'L',
            },
            LexType.Variable   : tuple('xyzv'),
            LexType.Constant   : tuple('mnos'),
            LexType.Quantifier : {
                Quantifier.Universal   : 'V',
                Quantifier.Existential : 'S',
            },
            (LexType.Predicate, True) : {
                Predicate.System.Identity.index  : 'I',
                Predicate.System.Existence.index : 'J',
                (Operator.Negation, Predicate.System.Identity): NotImplemented,
            },
            (LexType.Predicate, False) : tuple('FGHO'),
            Marking.paren_open  : (NotImplemented,),
            Marking.paren_close : (NotImplemented,),
            Marking.whitespace  : (' ',),
            Marking.meta: metachar['html'],
            Marking.tableau: tabsym['html'],
            Marking.subscript: subsym['html'],
        },
    )

    data[Notation.polish]['unicode'] = prev = dmerged(prev, dict(
        format  = 'unicode',
        strings  = dunesc(prev['strings']) | {
            Marking.subscript: subsym['unicode']
        },
    ))

    data[Notation.polish]['rst'] = prev = dmerged(prev, dict(
        format  = 'rst',
        strings = {Marking.subscript: subsym['rst']}
    ))

    data[Notation.polish]['ascii'] = prev = dmerged(prev, dict(
        format  = 'ascii',
        strings  = {
            Marking.meta: metachar['ascii'],
            Marking.tableau: tabsym['ascii'],
            Marking.subscript: subsym['ascii'],
        },
    ))

    data[Notation.polish]['latex'] = dmerged(prev, dict(
        format  = 'latex',
        strings  = {
            Marking.meta: metachar['latex'],
            Marking.tableau: tabsym['latex'],
            Marking.subscript: subsym['latex'],
        }
    ))

    Notation.standard
    '---------------'

    data[Notation.standard]['html'] = prev = dict(
        notation = Notation.standard,
        format  = 'html',
        strings = {
            LexType.Atomic   : tuple('ABCDE'),
            LexType.Operator : {
                Operator.Assertion             : '&#9900;' ,#'&#9675;' ,
                Operator.Negation              : '&not;'   ,
                Operator.Conjunction           : '&and;'   ,
                Operator.Disjunction           : '&or;'    ,
                Operator.MaterialConditional   : '&sup;'   ,
                Operator.MaterialBiconditional : '&equiv;' ,
                Operator.Conditional           : '&rarr;'  ,
                Operator.Biconditional         : '&harr;'  ,
                Operator.Possibility           : '&#9671;' ,
                Operator.Necessity             : '&#9723;' ,
            },
            LexType.Variable   : tuple('xyzv'),
            LexType.Constant   : tuple('abcd'),
            LexType.Quantifier : {
                Quantifier.Universal   : '&forall;' ,
                Quantifier.Existential : '&exist;'  ,
            },
            (LexType.Predicate, True) : {
                Predicate.System.Identity.index  : '=',
                Predicate.System.Existence.index : 'E!',
                (Operator.Negation, Predicate.System.Identity): '&ne;',
            },
            (LexType.Predicate, False) : tuple('FGHO'),
            Marking.paren_open   : ('(',),
            Marking.paren_close  : (')',),
            Marking.whitespace   : (' ',),
            Marking.meta: metachar['html'],
            Marking.tableau: tabsym['html'],
            Marking.subscript: subsym['html'],
        },
    )

    data[Notation.standard]['unicode'] = prev = dmerged(prev, dict(
        format  = 'unicode',
        strings  = dunesc(prev['strings'])| {
            Marking.subscript: subsym['unicode']
        },
    ))

    data[Notation.standard]['rst'] = prev = dmerged(prev, dict(
        format  = 'rst',
        strings = {Marking.subscript: subsym['rst']}
    ))

    data[Notation.standard]['ascii'] = prev = dmerged(prev, dict(
        format  = 'ascii',
        strings = {
            LexType.Operator : {
                Operator.Assertion              :  '*',
                Operator.Negation               :  '~',
                Operator.Conjunction            :  '&',
                Operator.Disjunction            :  'V',
                Operator.MaterialConditional    :  '>',
                Operator.MaterialBiconditional  :  '<',
                Operator.Conditional            :  '$',
                Operator.Biconditional          :  '%',
                Operator.Possibility            :  'P',
                Operator.Necessity              :  'N',
            },
            LexType.Quantifier : {
                Quantifier.Universal   : 'L',
                Quantifier.Existential : 'X',
            },
            (LexType.Predicate, True) : {
                (Operator.Negation, Predicate.System.Identity): '!=',
            },
            Marking.meta: metachar['ascii'],
            Marking.tableau: tabsym['ascii'],
            Marking.subscript: subsym['ascii'],
        },
    ))

    data[Notation.standard]['latex'] = dmerged(prev, dict(
        format  = 'latex',
        strings = {
            LexType.Operator : {
                Operator.Assertion              :  '\\circ{}',
                Operator.Negation               :  '\\neg{}',
                Operator.Conjunction            :  '\\wedge{}',
                Operator.Disjunction            :  '\\vee{}',
                Operator.MaterialConditional    :  '\\supset{}',
                Operator.MaterialBiconditional  :  '\\equiv{}',
                Operator.Conditional            :  '\\rightarrow{}',
                Operator.Biconditional          :  '\\leftrightarrow{}',
                Operator.Possibility            :  '\\Diamond{}',
                Operator.Necessity              :  '\\Box{}',
            },
            LexType.Quantifier : {
                Quantifier.Universal   : '\\forall{}',
                Quantifier.Existential : '\\exists{}',
            },
            (LexType.Predicate, True) : {
                (Operator.Negation, Predicate.System.Identity): '\\neq{}',
            },
            Marking.meta: metachar['latex'],
            Marking.tableau: tabsym['latex'],
            Marking.subscript: subsym['latex'],
        },
    ))
    return data

def tdata():

    from pytableaux.lang import Atomic, Constant, Variable, Operator, Predicate, Quantifier, Marking, Notation

    strings={
        Operator.Assertion: 'T',
        Operator.Negation: 'N',
        Operator.Conjunction: 'K',
        Operator.Disjunction: 'A',
        Operator.MaterialConditional: 'C',
        Operator.MaterialBiconditional: 'E',
        Operator.Conditional: 'U',
        Operator.Biconditional: 'B',
        Operator.Possibility: 'M',
        Operator.Necessity: 'L',
        Quantifier.Universal: 'V',
        Quantifier.Existential: 'S',
        Predicate.Identity: 'I',
        Predicate.Existence: 'J',
        (Operator.Negation, Predicate.Identity): NotImplemented,
        (Atomic, 0) : 'a',
        (Atomic, 1) : 'b',
        (Atomic, 2) : 'c',
        (Atomic, 3) : 'd',
        (Atomic, 4) : 'e',
        (Variable, 0) : 'x',
        (Variable, 1) : 'y',
        (Variable, 2) : 'z',
        (Variable, 3) : 'v',
        (Constant, 0) : 'm',
        (Constant, 1) : 'n',
        (Constant, 2) : 'o',
        (Constant, 3) : 's',
        (Predicate, 0): 'F',
        (Predicate, 0): 'G',
        (Predicate, 0): 'H',
        (Predicate, 0): 'O',
        (Marking.paren_open, 0)  : NotImplemented,
        (Marking.paren_close, 0) : NotImplemented,
        (Marking.whitespace, 0)  : ' ',
        (Marking.subscript_open, 0): '<sub>',
        (Marking.subscript_close, 0): '</sub>',
        (Marking.tableau, 'designation', True) : '&oplus;',  # '\2295'
        (Marking.tableau, 'designation', False): '&ominus;', # '\2296'
        (Marking.tableau, 'flag', 'closure') : '&otimes;',   # '\2297'
        (Marking.tableau, 'flag', 'quit'): '&#9872;',        # '⚐', '\U+2690'
        (Marking.tableau, 'access', 'symmetric'): 'R&#9007;',# '⌯', '\U+232F'
        (Marking.tableau, 'access', 'transitive'): 'R+',
        (Marking.tableau, 'access', 'reflexive'): 'R&le;',
        (Marking.tableau, 'access', 'serial'): 'Rser',
        (Marking.tableau, 'access'): 'R',
        (Marking.meta, 'conseq')    : '&vdash;',
        (Marking.meta, 'nonconseq') : '&nvdash;',
        (Marking.meta, 'therefore') : '&there4;',
        (Marking.meta, 'ellipsis')  : '&hellip;'}
    strings.setdefault(Marking.whitespace, strings[Marking.whitespace, 0])
    strings.setdefault(Marking.subscript_open, strings[Marking.subscript_open, 0])
    strings.setdefault(Marking.subscript_close, strings[Marking.subscript_close, 0])
    strings.setdefault(Marking.paren_open, strings[Marking.paren_open, 0])
    strings.setdefault(Marking.paren_close, strings[Marking.paren_close, 0])
    strings.setdefault((Marking.tableau, 'closure', True), strings[Marking.tableau, 'flag', 'closure'])
    tbl = dict(
        format='html',
        notation=Notation.polish,
        strings=strings)
    return tbl





@closure
def dtransform():

    def _true(_): True

    def api(transformer: Callable[[Any], Any], a: Mapping, /,
        typeinfo: type|tuple[type, ...] = dict,
        inplace = False,
    ) -> dict:

        if typeinfo is None:
            pred = _true
        else:
            pred = lambda v: isinstance(v, typeinfo)
        res = runner(transformer, pred, inplace, a)
        if not inplace:
            return res

    def runner(f, pred, inplace, a: Mapping):
        if inplace:
            b = a
        else:
            b = {}
        for k, v in a.items():
            if isinstance(v, Mapping):
                b[k] = runner(f, pred, inplace, v)
            elif pred(v):
                b[k] = f(v)
            else:
                b[k] = v
        return b

    return api


