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
pytableaux.examples
^^^^^^^^^^^^^^^^^^^

Example arguments
"""

from __future__ import annotations

__all__ = 'arguments', 'argument', 'tabiter'


from pytableaux import lexicals, parsers, tools

_args = tools.MapProxy({
    'Addition'                         : (('a',), 'Aab'),
    'Affirming a Disjunct 1'           : (('Aab', 'a'), 'b'),
    'Affirming a Disjunct 2'           : (('Aab', 'a'), 'Nb'),
    'Affirming the Consequent'         : (('Cab', 'b'), 'a'),
    'Assertion Elimination 1'          : (('Ta',), 'a' ),
    'Assertion Elimination 2'          : (('NTa',), 'Na'),
    'Biconditional Elimination 1'      : (('Bab', 'a'), 'b'),
    'Biconditional Elimination 2'      : (('Bab', 'Na'), 'Nb'),
    'Biconditional Elimination 3'      : (('NBab', 'a'), 'Nb'),
    'Biconditional Identity'           : 'Baa',
    'Biconditional Introduction 1'     : (('a', 'b'), 'Bab'),
    'Biconditional Introduction 2'     : (('Na', 'Nb'), 'Bab'),
    'Biconditional Introduction 3'     : (('a', 'Nb'), 'NBab'),
    'Conditional Contraction'          : (('UaUab',), 'Uab'),
    'Conditional Contraposition 1'     : (('Uab',), 'UNbNa'),
    'Conditional Contraposition 2'     : (('UNbNa',), 'Uab'),
    'Conditional Equivalence'          : (('Uab',), 'Uba'),
    'Conditional Identity'             : 'Uaa',
    'Conditional Modus Ponens'         : (('Uab', 'a'), 'b'),
    'Conditional Modus Tollens'        : (('Uab', 'Nb'), 'Na'),
    'Conditional Pseudo Contraction'   : 'UUaUabUab',
    'Conditional Pseudo Contraposition': 'BUabUNbNa',
    'Conjunction Commutativity'        : (('Kab',), 'Kba'),
    'Conjunction Elimination'          : (('Kab',), 'a'),
    'Conjunction Introduction'         : (('a', 'b'), 'Kab'),
    'Conjunction Pseudo Commutativity' : 'BKabKba',
    'DeMorgan 1'                       : (('NAab',), 'KNaNb'),
    'DeMorgan 2'                       : (('NKab',), 'ANaNb'),
    'DeMorgan 3'                       : (('KNaNb',), 'NAab'),
    'DeMorgan 4'                       : (('ANaNb',), 'NKab'),
    'DeMorgan 5'                       : (('Aab',), 'NKNaNb'),
    'DeMorgan 6'                       : (('Kab',), 'NANaNb'),
    'DeMorgan 7'                       : (('NKNaNb',), 'Aab'),
    'DeMorgan 8'                       : (('NANaNb',), 'Kab'),
    'Denying the Antecedent'           : (('Cab', 'Na'), 'b'),
    'Disjunction Commutativity'        : (('Aab',), 'Aba'),
    'Disjunction Pseudo Commutativity' : 'BAabAba',
    'Disjunctive Syllogism'            : (('Aab', 'Nb'), 'a'),
    'Disjunctive Syllogism 2'          : (('ANab', 'Nb'), 'Na'),
    'Existential from Universal'       : (('SxFx',), 'VxFx'),
    'Existential Syllogism'            : (('VxCFxGx', 'Fn'),  'Gn'),
    'Explosion'                        : (('KaNa',), 'b'),
    'Extracting a Disjunct 1'          : (('Aab',), 'b'),
    'Extracting a Disjunct 2'          : (('AaNb',), 'Na'),
    'Extracting the Antecedent'        : (('Cab',), 'a'),
    'Extracting the Consequent'        : (('Cab',), 'b'),
    'Identity Indiscernability 1'      : (('Fm', 'Imn'), 'Fn'),
    'Identity Indiscernability 2'      : (('Fm', 'Inm'), 'Fn'),
    'Law of Excluded Middle'           : 'AaNa',
    'Law of Non-contradiction'         : (('KaNa',), 'b'),
    'Material Biconditional Elimination 1' : (('Eab', 'a'), 'b'),
    'Material Biconditional Elimination 2' : (('Eab', 'Na'), 'Nb'),
    'Material Biconditional Elimination 3' : (('NEab', 'a'),  'Nb'),
    'Material Biconditional Identity'      : 'Eaa',
    'Material Biconditional Introduction 1': (('a', 'b'), 'Eab'),
    'Material Contraction'             : (('CaCab',), 'Cab'),
    'Material Contraposition 1'        : (('Cab',), 'CNbNa'),
    'Material Contraposition 2'        : (('CNbNa',), 'Cab'),
    'Material Identity'                : 'Caa',
    'Material Modus Ponens'            : (('Cab', 'a'), 'b'),
    'Material Modus Tollens'           : (('Cab', 'Nb'), 'Na'),
    'Material Pseudo Contraction'      : 'CCaCabCab',
    'Material Pseudo Contraposition'   : 'ECabCNbNa',
    'Modal Platitude 1'                : (('Ma',), 'Ma'),
    'Modal Platitude 2'                : (('La',), 'La'),
    'Modal Platitude 3'                : (('LMa',), 'LMa'),
    'Modal Transformation 1'           : (('La',), 'NMNa'),
    'Modal Transformation 2'           : (('NMNa',), 'La'),
    'Modal Transformation 3'           : (('NLa',), 'MNa'),
    'Modal Transformation 4'           : (('MNa',), 'NLa'),
    'Necessity Distribution 1'         : 'ULUabULaLb',
    'Necessity Distribution 2'         : (('LUab',), 'ULaLb'),
    'Necessity Elimination'            : (('La',), 'a'),
    'NP Collapse 1'                    : (('LMa',), 'Ma'),
    'Possibility Addition'             : (('a',), 'Ma'),
    'Possibility Distribution'         : (('KMaMb',), 'MKab'),
    'Quantifier Interdefinability 1'   : (('VxFx',), 'NSxNFx'),
    'Quantifier Interdefinability 2'   : (('NVxFx',), 'SxNFx'),
    'Quantifier Interdefinability 3'   : (('SxFx',), 'NVxNFx'),
    'Quantifier Interdefinability 4'   : (('NSxFx',), 'VxNFx'),
    'Reflexive Inference 1'            : 'CLaa',
    'S4 Conditional Inference 1'       : 'ULaLLa',
    'S4 Conditional Inference 2'       : (('LUaMNb', 'Ma'), 'MNb'),
    'S4 Material Inference 1'          : 'CLaLLa',
    'S4 Material Inference 2'          : (('LCaMNb', 'Ma'), 'MNb'),
    'S5 Conditional Inference 1'       : 'UaLMa',
    'S5 Material Inference 1'          : 'CaLMa',
    'Self Identity 1'                  : 'Imm',
    'Self Identity 2'                  : 'VxIxx',
    'Serial Inference 1'               : 'ULaMa',
    'Serial Inference 2'               : (('La',), 'Ma'),
    'Simplification'                   : (('Kab',), 'a'),
    'Syllogism'                        : (('VxCFxGx', 'VxCGxHx'), 'VxCFxHx'),
    'Triviality 1'                     : 'a',
    'Triviality 2'                     : (('a',), 'b'),
    'Universal Predicate Syllogism'    : (('VxVyCFxFy', 'Fm'), 'Fn'),
    'Universal from Existential'       : (('SxFx',), 'VxFx'),
})

_aliases = tools.MapProxy({
    'Triviality 1': ('TRIV', 'TRIV1'),
    'Triviality 2': ('TRIV2',),
    'Law of Excluded Middle': ('LEM',),
    'Law of Non-contradiction': ('LNC',),
    'Explosion': ('EFQ',),
    'Conditional Modus Ponens': ('MP','Modus Ponens'),
    'Conditional Modus Tollens': ('MT', 'Modus Tollens'),
    'Material Modus Ponens': ('MMP',),
    'Material Modus Tollens': ('MMT',),
    'Conditional Identity': ('Identity', 'ID'),
    'Conditional Contraction': ('Contraction',),
    'Disjunctive Syllogism': ('DS',),
    'DeMorgan 1': ('DM', 'DM1', 'DEM', 'DEM1', 'DeMorgan'),
    'DeMorgan 2': ('DM2', 'DEM2',),
    'DeMorgan 3': ('DM3', 'DEM3',),
    'DeMorgan 4': ('DM4', 'DEM4',),
    'DeMorgan 5': ('DM5', 'DEM5',),
    'DeMorgan 6': ('DM6', 'DEM6',),
    'DeMorgan 7': ('DM7', 'DEM7',),
    'DeMorgan 8': ('DM8', 'DEM8',),

    'Syllogism': ('SYL', 'SYLL'),
    'Quantifier Interdefinability 1': ('Q1',),
    'Quantifier Interdefinability 2': ('Q2',),
    'Quantifier Interdefinability 3': ('Q3',),
    'Quantifier Interdefinability 4': ('Q4',),

    'Modal Transformation 1': ('Modal 1',),
    'Modal Transformation 2': ('Modal 2',),
    'Modal Transformation 3': ('Modal 3',),
    'Modal Transformation 4': ('Modal 4',),

    'Serial Inference 1': ('SER', 'SER1', 'Serial', 'Serial 1', 'D'),
    'Serial Inference 2': ('SER2', 'Serial 2',),
    'Reflexive Inference 1': ('T', 'Reflexive', 'Reflexivity'),
    'S4 Material Inference 1': ('S4', 'S41', 'Transitive', 'RT', 'Transitivity'),
    'S4 Material Inference 2': ('S42',),
    'S5 Material Inference 1': ('S5', 'S51', 'RST'),
})

_titles = tuple(sorted(_args))

preds = lexicals.Predicates(((0,0,1), (1,0,1), (2,0,1)))

@tools.closure
def argument():

    index = {}
    cache = {}

    args = _args

    for name in args:
        index.update({
            k.lower(): name for k in (
                name,
                name.replace(' ', ''),
                *_aliases.get(name, ''),
            )
        })

    parsearg = parsers.Parser('polish', preds).argument

    def argument(key: str|lexicals.Argument) -> lexicals.Argument:
        if isinstance(key, lexicals.Argument):
            return key
        if not isinstance(key, str):
            raise TypeError(key)
        title = index[key.lower()]
        if title not in cache:
            info = args[title]
            if isinstance(info, tuple):
                premises, conclusion = info
            else:
                premises = None
                conclusion = info
            cache[title] = parsearg(conclusion, premises, title = title)
        return cache[title]

    return argument

@tools.closure
def arguments():

    titles = _titles

    def arguments(*keys: str|lexicals.Argument) -> tuple[lexicals.Argument, ...]:
        if not len(keys):
            keys = titles
        return tuple(map(argument, keys))

    return arguments

@tools.closure
def tabiter():

    titles = _titles

    def tabiter(*logics, build = True, **opts):
        if not len(logics):
            import pytableaux.logics
            logics = pytableaux.logics.__all__
        from pytableaux.proof.tableaux import Tableau
        for logic in logics:
            for title in titles:
                tab = Tableau(logic, argument(title), **opts)
                if build:
                    tab.build()
                yield tab

    return tabiter

del(
    tools,
    _aliases,
    _args,
    _titles,
)
