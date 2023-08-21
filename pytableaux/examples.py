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
pytableaux.examples
^^^^^^^^^^^^^^^^^^^

Example arguments
"""

from __future__ import annotations

from types import MappingProxyType as MapProxy
from typing import Mapping

from . import logics
from .errors import check
from .lang import Argument, Parser, Predicates
from .proof import Tableau
from .tools import closure

__all__ = (
    'aliases',
    'argument',
    'arguments',
    'data',
    'preds',
    'tabiter',
    'titles')

EMPTY = ()

data = MapProxy({
    'Addition'                         : (('a',), 'Aab'),
    'Affirming a Disjunct 1'           : (('Aab', 'a'), 'b'),
    'Affirming a Disjunct 2'           : (('Aab', 'a'), 'Nb'),
    'Affirming the Consequent'         : (('Cab', 'b'), 'a'),
    'Asserted Addition'                : (('a',), 'AaTb'),
    'Assertion Elimination 1'          : (('Ta',), 'a' ),
    'Assertion Elimination 2'          : (('NTa',), 'Na'),
    'Biconditional Elimination 1'      : (('Bab', 'a'), 'b'),
    'Biconditional Elimination 2'      : (('Bab', 'Na'), 'Nb'),
    'Biconditional Elimination 3'      : (('NBab', 'a'), 'Nb'),
    'Biconditional Identity'           : (EMPTY, 'Baa'),
    'Biconditional Introduction 1'     : (('a', 'b'), 'Bab'),
    'Biconditional Introduction 2'     : (('Na', 'Nb'), 'Bab'),
    'Biconditional Introduction 3'     : (('a', 'Nb'), 'NBab'),
    'Conditional Contraction'          : (('UaUab',), 'Uab', ('Contraction',)),
    'Conditional Contraposition 1'     : (('Uab',), 'UNbNa'),
    'Conditional Contraposition 2'     : (('UNbNa',), 'Uab'),
    'Conditional Double Negation'      : (EMPTY, 'UNNaa'),
    'Conditional Equivalence'          : (('Uab',), 'Uba'),
    'Conditional Identity'             : (EMPTY, 'Uaa', ('Identity', 'ID')),
    'Conditional Law of Excluded Middle': (EMPTY, 'AUabNUab', ('Conditional LEM',)),
    'Conditional Modus Ponens'         : (('Uab', 'a'), 'b', ('MP', 'Modus Ponens')),
    'Conditional Modus Tollens'        : (('Uab', 'Nb'), 'Na', ('MT', 'Modus Tollens')),
    'Conditional Pseudo Contraction'   : (EMPTY, 'UUaUabUab'),
    'Conditional Pseudo Contraposition': (EMPTY, 'BUabUNbNa'),
    'Conjunction Commutativity'        : (('Kab',), 'Kba'),
    'Conjunction Elimination'          : (('Kab',), 'a', ('Simplification',)),
    'Conjunction Introduction'         : (('a', 'b'), 'Kab'),
    'Conjunction Pseudo Commutativity' : (EMPTY, 'BKabKba'),
    'DeMorgan 1'                       : (('NAab',), 'KNaNb', ('DM', 'DM1', 'DEM', 'DEM1', 'DeMorgan')),
    'DeMorgan 2'                       : (('NKab',), 'ANaNb', ('DM2', 'DEM2')),
    'DeMorgan 3'                       : (('KNaNb',), 'NAab', ('DM3', 'DEM3')),
    'DeMorgan 4'                       : (('ANaNb',), 'NKab', ('DM4', 'DEM4')),
    'DeMorgan 5'                       : (('Aab',), 'NKNaNb', ('DM5', 'DEM5')),
    'DeMorgan 6'                       : (('Kab',), 'NANaNb', ('DM6', 'DEM6')),
    'DeMorgan 7'                       : (('NKNaNb',), 'Aab', ('DM7', 'DEM7')),
    'DeMorgan 8'                       : (('NANaNb',), 'Kab', ('DM8', 'DEM8')),
    'Denying the Antecedent'           : (('Cab', 'Na'), 'b'),
    'Disjunction Commutativity'        : (('Aab',), 'Aba'),
    'Disjunction Pseudo Commutativity' : (EMPTY, 'BAabAba'),
    'Disjunctive Syllogism'            : (('Aab', 'Nb'), 'a', ('DS',)),
    'Disjunctive Syllogism 2'          : (('ANab', 'Nb'), 'Na'),
    'Existential from Universal'       : (('VxFx',), 'SxFx'),
    'Existential Syllogism'            : (('VxCFxGx', 'Fn'),  'Gn'),
    'Explosion'                        : (('KaNa',), 'b', ('EFQ',)),
    'Extracting a Disjunct 1'          : (('Aab',), 'b'),
    'Extracting a Disjunct 2'          : (('AaNb',), 'Na'),
    'Extracting the Antecedent'        : (('Cab',), 'a'),
    'Extracting the Consequent'        : (('Cab',), 'b'),
    'Identity Indiscernability 1'      : (('Fm', 'Imn'), 'Fn'),
    'Identity Indiscernability 2'      : (('Fm', 'Inm'), 'Fn'),
    'Law of Excluded Middle'           : (EMPTY, 'AaNa', ('LEM',)),
    'Law of Non-contradiction'         : (('KaNa',), 'b', ('LNC',)),
    'Material Biconditional Elimination 1' : (('Eab', 'a'), 'b'),
    'Material Biconditional Elimination 2' : (('Eab', 'Na'), 'Nb'),
    'Material Biconditional Elimination 3' : (('NEab', 'a'),  'Nb'),
    'Material Biconditional Identity'      : (EMPTY, 'Eaa'),
    'Material Biconditional Introduction 1': (('a', 'b'), 'Eab'),
    'Material Contraction'             : (('CaCab',), 'Cab'),
    'Material Contraposition 1'        : (('Cab',), 'CNbNa'),
    'Material Contraposition 2'        : (('CNbNa',), 'Cab'),
    'Material Identity'                : (EMPTY, 'Caa'),
    'Material Modus Ponens'            : (('Cab', 'a'), 'b', ('MMP',)),
    'Material Modus Tollens'           : (('Cab', 'Nb'), 'Na', ('MMT',)),
    'Material Pseudo Contraction'      : (EMPTY, 'CCaCabCab'),
    'Material Pseudo Contraposition'   : (EMPTY, 'ECabCNbNa'),
    'Modal Platitude 1'                : (('Ma',), 'Ma'),
    'Modal Platitude 2'                : (('La',), 'La'),
    'Modal Platitude 3'                : (('LMa',), 'LMa'),
    'Modal Transformation 1'           : (('La',), 'NMNa', ('Modal 1',)),
    'Modal Transformation 2'           : (('NMNa',), 'La', ('Modal 2',)),
    'Modal Transformation 3'           : (('NLa',), 'MNa', ('Modal 3',)),
    'Modal Transformation 4'           : (('MNa',), 'NLa', ('Modal 4',)),
    'Necessity Distribution 1'         : (EMPTY, 'ULUabULaLb'),
    'Necessity Distribution 2'         : (('LUab',), 'ULaLb'),
    'Necessity Elimination'            : (('La',), 'a'),
    'NP Collapse 1'                    : (('LMa',), 'Ma'),
    'Possibility Addition'             : (('a',), 'Ma'),
    'Possibility Distribution'         : (('KMaMb',), 'MKab'),
    'Quantifier Interdefinability 1'   : (('VxFx',), 'NSxNFx', ('Q1',)),
    'Quantifier Interdefinability 2'   : (('NVxFx',), 'SxNFx', ('Q2',)),
    'Quantifier Interdefinability 3'   : (('SxFx',), 'NVxNFx', ('Q3',)),
    'Quantifier Interdefinability 4'   : (('NSxFx',), 'VxNFx', ('Q4',)),
    'Reflexive Inference 1'            : (EMPTY, 'CLaa', ('T', 'Reflexive', 'Reflexivity')),
    'S4 Conditional Inference 1'       : (EMPTY, 'ULaLLa'),
    'S4 Conditional Inference 2'       : (('LUaMNb', 'Ma'), 'MNb'),
    'S4 Material Inference 1'          : (EMPTY, 'CLaLLa', ('S4', 'S41', 'Transitive', 'RT', 'Transitivity')),
    'S4 Material Inference 2'          : (('LCaMNb', 'Ma'), 'MNb', ('S42',)),
    'S5 Conditional Inference 1'       : (EMPTY, 'UaLMa'),
    'S5 Material Inference 1'          : (EMPTY, 'CaLMa', ('S5', 'S51', 'RST')),
    'Self Identity 1'                  : (EMPTY, 'Imm'),
    'Self Identity 2'                  : (EMPTY, 'VxIxx'),
    'Serial Inference 1'               : (EMPTY, 'ULaMa', ('SER', 'SER1', 'Serial', 'Serial 1', 'D')),
    'Serial Inference 2'               : (('La',), 'Ma', ('SER2', 'Serial 2',)),
    'Syllogism'                        : (('VxCFxGx', 'VxCGxHx'), 'VxCFxHx', ('SYL', 'SYLL')),
    'Triviality 1'                     : (EMPTY, 'a', ('TRIV', 'TRIV1')),
    'Triviality 2'                     : (('a',), 'b', ('TRIV2',)),
    'Universal Predicate Syllogism'    : (('VxVyCFxFy', 'Fm'), 'Fn'),
    'Universal from Existential'       : (('SxFx',), 'VxFx'),
})

preds = Predicates(((0,0,1), (1,0,1), (2,0,1)))

class Arguments:

    def __init__(self, data: Mapping[str, tuple], preds=None, parser=None):
        self.index = {}
        self.cache = {}
        if not parser:
            if not preds:
                preds = Predicates(((0,0,1), (1,0,1), (2,0,1)))
            parser = Parser('polish', preds)
        self.parser = parser
    ...



titles = tuple(sorted(data))


@closure
def argument():

    index = {}
    cache = {}

    for name, entry in data.items():
        try:
            aliases = entry[2]
        except IndexError:
            aliases = EMPTY
        index.update({
            k: name for k in (name, *aliases)})

    parsearg = Parser('polish', preds.copy()).argument

    def argument(key) -> Argument:
        if isinstance(key, Argument):
            return key
        key = check.inst(key, str)
        title = index[key]
        if title not in cache:
            premises, conclusion, *_ = data[title]
            cache[title] = parsearg(conclusion, premises, title = title)
        return cache[title]

    return argument

def arguments(*keys):
    if not len(keys):
        keys = titles
    return tuple(map(argument, keys))


def tabiter(*logics, build = True, grouparg = False, registry = logics.registry, shuffle=False, **opts):
    if not len(logics):
        logics = tuple(registry.all())
    if grouparg:
        it = ((logic, title) for title in titles for logic in logics)
    else:
        it = ((logic, title) for logic in logics for title in titles)
    if shuffle:
        import random
        it = list(it)
        random.shuffle(it)
    for logic, title in it:
        tab = Tableau(logic, argument(title), **opts)
        if build:
            tab.build()
        yield tab
