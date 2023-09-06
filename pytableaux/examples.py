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

from .lang import Argument
from .logics import registry
from .proof import Tableau

__all__ = (
    'args',
    'tabiter')

args = MapProxy(dict((key, Argument(value, title=key)) for key, value in {
    'Addition'                         : 'Aab:a',
    'Affirming a Disjunct 1'           : 'b:Aab:a',
    'Affirming a Disjunct 2'           : 'Nb:Aab:a',
    'Affirming the Consequent'         : 'a:Cab:b',
    'Asserted Addition'                : 'AaTb:a',
    'Assertion Elimination 1'          : 'a:Ta',
    'Assertion Elimination 2'          : 'Na:NTa',
    'Biconditional Elimination 1'      : 'b:Bab:a',
    'Biconditional Elimination 2'      : 'Nb:Bab:Na',
    'Biconditional Elimination 3'      : 'Nb:NBab:a',
    'Biconditional Identity'           : 'Baa',
    'Biconditional Introduction 1'     : 'Bab:a:b',
    'Biconditional Introduction 2'     : 'Bab:Na:Nb',
    'Biconditional Introduction 3'     : 'NBab:a:Nb',
    'Conditional Contraction'          : 'Uab:UaUab',
    'Conditional Contraposition 1'     : 'UNbNa:Uab',
    'Conditional Contraposition 2'     : 'Uab:UNbNa',
    'Conditional Double Negation'      : 'UNNaa',
    'Conditional Equivalence'          : 'Uba:Uab',
    'Conditional Identity'             : 'Uaa',
    'Conditional Law of Excluded Middle': 'AUabNUab',
    'Conditional Modus Ponens'         : 'b:Uab:a',
    'Conditional Modus Tollens'        : 'Na:Uab:Nb',
    'Conditional Pseudo Contraction'   : 'UUaUabUab',
    'Conditional Pseudo Contraposition': 'BUabUNbNa',
    'Conjunction Commutativity'        : 'Kba:Kab',
    'Conjunction Elimination'          : 'a:Kab',
    'Conjunction Introduction'         : 'Kab:a:b',
    'Conjunction Pseudo Commutativity' : 'BKabKba',
    'DeMorgan 1'                       : 'KNaNb:NAab',
    'DeMorgan 2'                       : 'ANaNb:NKab',
    'DeMorgan 3'                       : 'NAab:KNaNb',
    'DeMorgan 4'                       : 'NKab:ANaNb',
    'DeMorgan 5'                       : 'NKNaNb:Aab',
    'DeMorgan 6'                       : 'NANaNb:Kab',
    'DeMorgan 7'                       : 'Aab:NKNaNb',
    'DeMorgan 8'                       : 'Kab:NANaNb',
    'Denying the Antecedent'           : 'b:Cab:Na',
    'Disjunction Commutativity'        : 'Aba:Aab',
    'Disjunction Pseudo Commutativity' : 'BAabAba',
    'Disjunctive Syllogism 2'          : 'Na:ANab:Nb',
    'Disjunctive Syllogism'            : 'a:Aab:Nb',
    'Existential from Universal'       : 'SxFx:VxFx',
    'Existential Syllogism'            : 'Gn:VxCFxGx:Fn',
    'Explosion'                        : 'b:KaNa',
    'Extracting a Disjunct 1'          : 'b:Aab',
    'Extracting a Disjunct 2'          : 'Na:AaNb',
    'Extracting the Antecedent'        : 'a:Cab',
    'Extracting the Consequent'        : 'b:Cab',
    'Identity Indiscernability 1'      : 'Fn:Fm:Imn',
    'Identity Indiscernability 2'      : 'Fn:Fm:Inm',
    'KFDE Distribution Inference 1'    : 'MKaNb:KLaNLb',
    'Law of Excluded Middle'           : 'AaNa',
    'Law of Non-contradiction'         : 'b:KaNa',
    'Material Biconditional Elimination 1' : 'b:Eab:a',
    'Material Biconditional Elimination 2' : 'Nb:Eab:Na',
    'Material Biconditional Elimination 3' : 'Nb:NEab:a',
    'Material Biconditional Identity'      : 'Eaa',
    'Material Biconditional Introduction 1': 'Eab:a:b',
    'Material Contraction'             : 'Cab:CaCab',
    'Material Contraposition 1'        : 'CNbNa:Cab',
    'Material Contraposition 2'        : 'Cab:CNbNa',
    'Material Identity'                : 'Caa',
    'Material Modus Ponens'            : 'b:Cab:a',
    'Material Modus Tollens'           : 'Na:Cab:Nb',
    'Material Pseudo Contraction'      : 'CCaCabCab',
    'Material Pseudo Contraposition'   : 'ECabCNbNa',
    'Modal Platitude 1'                : 'Ma:Ma',
    'Modal Platitude 2'                : 'La:La',
    'Modal Platitude 3'                : 'LMa:LMa',
    'Modal Transformation 1'           : 'NMNa:La',
    'Modal Transformation 2'           : 'La:NMNa',
    'Modal Transformation 3'           : 'MNa:NLa',
    'Modal Transformation 4'           : 'NLa:MNa',
    'Necessity Distribution 1'         : 'ULUabULaLb',
    'Necessity Distribution 2'         : 'ULaLb:LUab',
    'Necessity Elimination'            : 'a:La',
    'NP Collapse 1'                    : 'Ma:LMa',
    'NP Conditional Modus Ponens'      : 'Mb:LUab:Ma',
    'Possibility Addition'             : 'Ma:a',
    'Possibility Distribution'         : 'MKab:KMaMb',
    'Quantifier Interdefinability 1'   : 'NSxNFx:VxFx',
    'Quantifier Interdefinability 2'   : 'SxNFx:NVxFx',
    'Quantifier Interdefinability 3'   : 'NVxNFx:SxFx',
    'Quantifier Interdefinability 4'   : 'VxNFx:NSxFx',
    'Reflexive Inference 1'            : 'CLaa',
    'S4 Conditional Inference 1'       : 'ULaLLa',
    'S4 Conditional Inference 2'       : 'MNb:LUaMNb:Ma',
    'S4 Material Inference 1'          : 'CLaLLa',
    'S4 Material Inference 2'          : 'MNb:LCaMNb:Ma',
    'S5 Conditional Inference 1'       : 'UaLMa',
    'S5 Inference 1'                   : 'LMa:a',
    'S5 Material Inference 1'          : 'CaLMa',
    'Self Identity 1'                  : 'Imm',
    'Self Identity 2'                  : 'VxIxx',
    'Serial Inference 1'               : 'ULaMa',
    'Serial Inference 2'               : 'Ma:La',
    'Syllogism'                        : 'VxCFxHx:VxCFxGx:VxCGxHx',
    'Triviality 1'                     : 'a',
    'Triviality 2'                     : 'b:a',
    'Universal from Existential'       : 'VxFx:SxFx',
    'Universal Predicate Syllogism'    : 'Fn:VxVyCFxFy:Fm',
}.items()))


def tabiter(*logics, build=True, grouparg=False, registry=registry, shuffle=False, **opts):
    if not len(logics):
        logics = tuple(registry.all())
    if grouparg:
        it = ((logic, arg) for arg in args.values() for logic in logics)
    else:
        it = ((logic, arg) for logic in logics for arg in args.values())
    if shuffle:
        import random
        it = list(it)
        random.shuffle(it)
    for logic, arg in it:
        tab = Tableau(logic, arg, **opts)
        if build:
            tab.build()
        yield tab
