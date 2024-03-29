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

from html import unescape as html_unescape
from typing import Mapping

__all__ = ()


def parse_tables():
    from . import (Atomic, Constant, Marking, Notation, Operator, Predicate,
                   Quantifier, Variable)

    yield dict(
        notation = Notation.standard,
        mapping = {
            '*' : (Operator, Operator.Assertion),
            '~' : (Operator, Operator.Negation),
            '&' : (Operator, Operator.Conjunction),
            'V' : (Operator, Operator.Disjunction),
            '>' : (Operator, Operator.MaterialConditional),
            '<' : (Operator, Operator.MaterialBiconditional),
            '$' : (Operator, Operator.Conditional),
            '%' : (Operator, Operator.Biconditional),
            'P' : (Operator, Operator.Possibility),
            'N' : (Operator, Operator.Necessity),
            'X' : (Quantifier, Quantifier.Existential),
            'L' : (Quantifier, Quantifier.Universal),
            '!' : (Predicate.System, Predicate.Existence),
            '=' : (Predicate.System, Predicate.Identity),
            'x' : (Variable, 0),
            'y' : (Variable, 1),
            'z' : (Variable, 2),
            'v' : (Variable, 3),
            'a' : (Constant, 0),
            'b' : (Constant, 1),
            'c' : (Constant, 2),
            'd' : (Constant, 3),
            'F' : (Predicate, 0),
            'G' : (Predicate, 1),
            'H' : (Predicate, 2),
            'O' : (Predicate, 3),
            'A' : (Atomic, 0),
            'B' : (Atomic, 1),
            'C' : (Atomic, 2),
            'D' : (Atomic, 3),
            'E' : (Atomic, 4),
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
            '9' : (Marking.digit, 9)})
    yield dict(
        notation = Notation.polish,
        mapping = {
            'T' : (Operator, Operator.Assertion),
            'N' : (Operator, Operator.Negation),
            'K' : (Operator, Operator.Conjunction),
            'A' : (Operator, Operator.Disjunction),
            'C' : (Operator, Operator.MaterialConditional),
            'E' : (Operator, Operator.MaterialBiconditional),
            'U' : (Operator, Operator.Conditional),
            'B' : (Operator, Operator.Biconditional),
            'M' : (Operator, Operator.Possibility),
            'L' : (Operator, Operator.Necessity),
            'S' : (Quantifier, Quantifier.Existential),
            'V' : (Quantifier, Quantifier.Universal),
            'J' : (Predicate.System, Predicate.Existence),
            'I' : (Predicate.System, Predicate.Identity),
            'x' : (Variable, 0),
            'y' : (Variable, 1),
            'z' : (Variable, 2),
            'v' : (Variable, 3),
            'm' : (Constant, 0),
            'n' : (Constant, 1),
            'o' : (Constant, 2),
            's' : (Constant, 3),
            'F' : (Predicate, 0),
            'G' : (Predicate, 1),
            'H' : (Predicate, 2),
            'O' : (Predicate, 3),
            'a' : (Atomic, 0),
            'b' : (Atomic, 1),
            'c' : (Atomic, 2),
            'd' : (Atomic, 3),
            'e' : (Atomic, 4),
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
            '9' : (Marking.digit, 9)})

def string_tables():


    from . import (Atomic, Constant, Marking, Notation, Operator, Predicate,
                   Quantifier, Variable)
    
    # tab symbols
    markings = dict(
        ascii = {
            (Marking.subscript_open, 0): '',
            (Marking.subscript_close, 0): '',
            (Marking.tableau, 'designation', True) :  '[+]',
            (Marking.tableau, 'designation', False):  '[-]',
            (Marking.tableau, 'flag', 'closure') : '(x)',
            (Marking.tableau, 'flag', 'quit') : '(q)',
            (Marking.tableau, 'access', 'symmetric') : 'R(sym)',
            (Marking.tableau, 'access', 'transitive') : 'R(+)',
            (Marking.tableau, 'access', 'reflexive'): 'R(<=)',
            (Marking.tableau, 'access', 'serial'): 'R(ser)',
            (Marking.tableau, 'access'): 'R',
            (Marking.meta, 'conseq')    : '|-',
            (Marking.meta, 'nonconseq') : '|/-',
            (Marking.meta, 'therefore') : ':.',
            (Marking.meta, 'ellipsis')  : '...',
        },
        html = {
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
            (Marking.meta, 'ellipsis')  : '&hellip;',
        },
        latex = {
            (Marking.subscript_open, 0): '_{',
            (Marking.subscript_close, 0): '}',
            (Marking.tableau, 'designation', True) : '\\varoplus{}',
            (Marking.tableau, 'designation', False) : '\\varominus{}',
            (Marking.tableau, 'flag', 'closure') : '\\varotimes{}',
            (Marking.tableau, 'flag', 'quit') : '\\bowtie{}',
            (Marking.tableau, 'access', 'symmetric') : '\\mathcal{R}_{sym}',
            (Marking.tableau, 'access', 'transitive') : '\\mathcal{R}_{+}',
            (Marking.tableau, 'access', 'reflexive') : '\\mathcal{R}_{\\leq{}}',
            (Marking.tableau, 'access', 'serial') : '\\mathcal{R}_{ser}',
            (Marking.tableau, 'access'): '\\mathcal{R}',
            (Marking.meta, 'conseq')    : '\\Vdash{}',
            (Marking.meta, 'nonconseq') : '\\nVdash{}',
            (Marking.meta, 'therefore') : '\\therefore{}',
            (Marking.meta, 'ellipsis')  : '\\ldots{}',
        })

    markings['unicode'] = dunesc(markings['html']) | {
        (Marking.subscript_open, 0): '.[',
        (Marking.subscript_close, 0): ']',
    }

    markings['rst'] = dict(markings['unicode']) | {
        (Marking.subscript_open, 0): ':sub:`',
        (Marking.subscript_close, 0): '`',
    }

    polish_strings = dict(
        ascii = {
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
            (Predicate, 1): 'G',
            (Predicate, 2): 'H',
            (Predicate, 3): 'O',
            (Marking.paren_open, 0)  : NotImplemented,
            (Marking.paren_close, 0) : NotImplemented,
            (Marking.whitespace, 0)  : ' ',})

    standard_strings = dict(
        html = {
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
            Quantifier.Universal   : '&forall;' ,
            Quantifier.Existential : '&exist;'  ,
            Predicate.Identity: '=',
            Predicate.Existence: 'E!',
            (Operator.Negation, Predicate.Identity): '&ne;',
            (Atomic, 0) : 'A',
            (Atomic, 1) : 'B',
            (Atomic, 2) : 'C',
            (Atomic, 3) : 'D',
            (Atomic, 4) : 'E',
            (Variable, 0) : 'x',
            (Variable, 1) : 'y',
            (Variable, 2) : 'z',
            (Variable, 3) : 'v',
            (Constant, 0) : 'a',
            (Constant, 1) : 'b',
            (Constant, 2) : 'c',
            (Constant, 3) : 'd',
            (Predicate, 0): 'F',
            (Predicate, 1): 'G',
            (Predicate, 2): 'H',
            (Predicate, 3): 'O',
            (Marking.paren_open, 0)  : '(',
            (Marking.paren_close, 0) : ')',
            (Marking.whitespace, 0)  : ' ',})

    standard_strings['unicode'] = dunesc(standard_strings['html'])

    standard_strings['ascii'] = standard_strings['unicode'] | {
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
        Quantifier.Universal   : 'L',
        Quantifier.Existential : 'X',
        (Operator.Negation, Predicate.Identity): '!='}

    standard_strings['latex'] = standard_strings['unicode'] | {
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
        Quantifier.Universal   : '\\forall{}',
        Quantifier.Existential : '\\exists{}',
        (Operator.Negation, Predicate.Identity): '\\neq{}'}

    yield dict(
        format = 'text',
        dialect = 'ascii',
        notation = Notation.polish,
        strings = polish_strings['ascii'] | markings['ascii'])

    yield dict(
        format = 'text',
        dialect = 'unicode',
        notation = Notation.polish,
        strings = polish_strings['ascii'] | markings['unicode'])

    yield dict(
        format = 'html',
        dialect = 'html',
        notation = Notation.polish,
        strings = polish_strings['ascii'] | markings['html'])

    yield dict(
        format = 'rst',
        dialect = 'rst',
        notation = Notation.polish,
        strings = polish_strings['ascii'] | markings['rst'])

    yield dict(
        format = 'latex',
        dialect = 'latex',
        notation = Notation.polish,
        strings = polish_strings['ascii'] | markings['latex'])

    yield dict(
        format  = 'text',
        dialect = 'ascii',
        notation = Notation.standard,
        strings = standard_strings['ascii'] | markings['ascii'])

    yield dict(
        format  = 'text',
        dialect = 'unicode',
        notation = Notation.standard,
        strings = standard_strings['unicode'] | markings['unicode'])

    yield dict(
        format  = 'html',
        dialect = 'html',
        notation = Notation.standard,
        strings = standard_strings['html'] | markings['html'])

    yield dict(
        format  = 'rst',
        dialect = 'rst',
        notation = Notation.standard,
        strings = standard_strings['unicode'] | markings['rst'])

    yield dict(
        format = 'latex',
        dialect = 'latex',
        notation = Notation.standard,
        strings = standard_strings['latex'] | markings['latex'])


def dunesc(d: Mapping) -> None:
    return {key: html_unescape(value) for key, value in d.items()}
