# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - example arguments

from lexicals import Predicate, Predicates, Constant, Variable, Atomic, \
    Predicated, Operated, Quantified
from parsers import create_parser
from utils import isstr
from itertools import chain
import re

# polish notation
args = {
    'Addition'                         : [[ 'a' ], 'Aab'   ],
    'Affirming a Disjunct 1'           : [[ 'Aab', 'a'  ], 'b'  ],
    'Affirming a Disjunct 2'           : [[ 'Aab', 'a'  ], 'Nb' ],
    'Affirming the Consequent'         : [[ 'Cab', 'b'  ], 'a'  ],
    'Assertion Elimination 1'          : [[ 'Ta' ], 'a'   ],
    'Assertion Elimination 2'          : [[ 'NTa' ], 'Na' ],
    'Biconditional Elimination 1'      : [[ 'Bab', 'a'  ], 'b'  ],
    'Biconditional Elimination 2'      : [[ 'Bab', 'Na' ], 'Nb' ],
    'Biconditional Elimination 3'      : [[ 'NBab', 'a'],  'Nb'],
    'Biconditional Identity'           : 'Baa',
    'Biconditional Introduction 1'     : [[ 'a', 'b'   ], 'Bab'],
    'Biconditional Introduction 2'     : [[ 'Na', 'Nb' ], 'Bab'],
    'Biconditional Introduction 3'     : [[ 'a', 'Nb'  ], 'NBab'],
    'Conditional Contraction'          : [[ 'UaUab' ], 'Uab'   ],
    'Conditional Equivalence'          : [[ 'Uab'   ], 'Uba'  ],
    'Conditional Identity'             : 'Uaa',
    'Conditional Modus Ponens'         : [[ 'Uab', 'a'  ], 'b'  ],
    'Conditional Modus Tollens'        : [[ 'Uab', 'Nb' ], 'Na' ],
    'Conditional Pseudo Contraction'   : 'UUaUabUab',
    'Conjunction Introduction'         : [[ 'a', 'b' ],  'Kab'],
    'DeMorgan 1'                       : [[ 'NAab'  ], 'KNaNb' ],
    'DeMorgan 2'                       : [[ 'NKab'  ], 'ANaNb' ],
    'DeMorgan 3'                       : [[ 'KNaNb' ], 'NAab'  ],
    'DeMorgan 4'                       : [[ 'ANaNb' ], 'NKab'  ],
    'DeMorgan 5'                       : [[ 'Aab'   ], 'NKNaNb' ],
    'DeMorgan 6'                       : [[ 'Kab'   ], 'NANaNb' ],
    'DeMorgan 7'                       : [[ 'NKNaNb' ], 'Aab' ],
    'DeMorgan 8'                       : [[ 'NANaNb' ], 'Kab' ],
    'Denying the Antecedent'           : [[ 'Cab', 'Na' ], 'b'  ],
    'Disjunctive Syllogism'            : [[ 'Aab', 'Nb' ], 'a'  ],
    'Disjunctive Syllogism 2'          : [[ 'ANab', 'Nb'], 'Na' ],
    'Existential from Universal'       : [[ 'SxFx' ], 'VxFx' ],
    'Existential Syllogism'            : [[ 'VxCFxGx', 'Fn'  ],  'Gn'],
    'Explosion'                        : [[ 'KaNa' ], 'b' ],
    'Extracting a Disjunct 1'          : [[ 'Aab'  ], 'b'    ],
    'Extracting a Disjunct 2'          : [[ 'AaNb' ], 'Na'   ],
    'Extracting the Antecedent'        : [[ 'Cab'  ], 'a'    ],
    'Extracting the Consequent'        : [[ 'Cab'  ], 'b'    ],
    'Identity Indiscernability 1'      : [[ 'Fm', 'Imn' ], 'Fn' ],
    'Identity Indiscernability 2'      : [[ 'Fm', 'Inm' ], 'Fn' ],
    'Law of Excluded Middle'           : 'AaNa',
    'Law of Non-contradiction'         : [[ 'KaNa' ], 'b'  ],
    'Material Biconditional Elimination 1' : [[ 'Eab', 'a'  ], 'b'  ],
    'Material Biconditional Elimination 2' : [[ 'Eab', 'Na' ], 'Nb' ],
    'Material Biconditional Elimination 3' : [[ 'NEab', 'a'],  'Nb'],
    'Material Biconditional Identity'  : 'Eaa',
    'Material Biconditional Introduction 1': [[ 'a', 'b' ], 'Eab' ],
    'Material Contraction'             : [[ 'CaCab' ], 'Cab'   ],
    'Material Identity'                : 'Caa',
    'Material Modus Ponens'            : [[ 'Cab', 'a'  ], 'b'  ],
    'Material Modus Tollens'           : [[ 'Cab', 'Nb' ], 'Na' ],
    'Material Pseudo Contraction'      : 'CCaCabCab',
    'Modal Platitude 1'                : [[ 'Ma'   ], 'Ma'   ],
    'Modal Platitude 2'                : [[ 'La'   ], 'La'   ],
    'Modal Platitude 3'                : [[ 'LMa'  ], 'LMa'  ],
    'Modal Transformation 1'           : [[ 'La'   ], 'NMNa' ],
    'Modal Transformation 2'           : [[ 'NMNa' ], 'La'   ],
    'Modal Transformation 3'           : [[ 'NLa'  ], 'MNa'  ],
    'Modal Transformation 4'           : [[ 'MNa'  ], 'NLa'  ],
    'Necessity Distribution 1'         : 'ULUabULaLb',
    'Necessity Distribution 2'         : [['LUab'], 'ULaLb'],
    'Necessity Elimination'            : [[ 'La'  ], 'a' ],
    'NP Collapse 1'                    : [[ 'LMa' ], 'Ma'],
    'Possibility Addition'             : [[ 'a'   ], 'Ma'],
    'Possibility Distribution'         : [[ 'KMaMb' ], 'MKab'],
    'Quantifier Interdefinability 1'   : [[ 'VxFx'  ], 'NSxNFx' ],
    'Quantifier Interdefinability 2'   : [[ 'NVxFx' ], 'SxNFx'  ],
    'Quantifier Interdefinability 3'   : [[ 'SxFx'  ], 'NVxNFx' ],
    'Quantifier Interdefinability 4'   : [[ 'NSxFx' ], 'VxNFx'  ],
    'Reflexive Inference 1'            : 'CLaa',
    'S4 Conditional Inference 1'       : 'ULaLLa',
    'S4 Conditional Inference 2'       : [['LUaMNb', 'Ma'], 'MNb'],
    'S4 Material Inference 1'          : 'CLaLLa',
    'S4 Material Inference 2'          : [['LCaMNb', 'Ma'], 'MNb'],
    'S5 Conditional Inference 1'       : 'UaLMa',
    'S5 Material Inference 1'          : 'CaLMa',
    'Self Identity 1'                  : 'Imm',
    'Self Identity 2'                  : 'VxIxx',
    'Serial Inference 1'               : 'ULaMa',
    'Serial Inference 2'               : [['La'], 'Ma'],
    'Simplification'                   : [[ 'Kab' ], 'a' ],
    'Syllogism'                        : [[ 'VxCFxGx', 'VxCGxHx' ], 'VxCFxHx'],
    'Triviality 1'                     : 'a',
    'Triviality 2'                     : [[ 'a' ], 'b' ],
    'Universal Predicate Syllogism'    : [[ 'VxVyCFxFy', 'Fm'], 'Fn'],
    'Universal from Existential'       : [[ 'SxFx' ], 'VxFx' ],
}

args_list = sorted(args.keys())

# Test vocabulary predicate data
# test_pred_data = [
#     [0, 0, 1],
#     [1, 0, 1],
#     [2, 0, 1],
# ]

preds = vocab = vocabulary = Predicates(*Predicate.gen(3))
parser = create_parser(notn='polish', vocab=vocab)

aliases = {
    'Law of Excluded Middle': ('LEM',),
    'Law of Non-contradiction': ('LNC',),
    'Explosion': ('EFQ',),
    'Conditional Modus Ponens': ('MP','Modus Ponens'),
    'Conditional Modus Tollens': ('MT', 'Modus Tollens'),
    'Material Modus Ponens': ('MMP',),
    'Material Modus Tollens': ('MMT',),
}
_idx = {}
for name in args:
    _idx.update({
        k.lower(): name for k in (
            name, re.sub(' ','', name), *aliases.get(name, set())
        )
    })

def argument(key):
    title = _idx[key.lower()]
    info = args[title]
    if isinstance(info, list):
        premises, conclusion = info
    else:
        premises = []
        conclusion = info
    return parser.argument(conclusion, premises, title=title)

def arguments(names=None):
    if names == None:
        names = args_list
    return [argument(name) for name in names]

def predicated():
    return Predicated.first()

def identity():
    return Predicate.Identity(tuple([*Constant.gen(2)]))

def self_identity():
    a = Constant.first()
    return Predicate.Identity((a, a))

def existence():
    return Predicate.Identity((Constant.first(),))

def quantified(quantifier):
    return Quantified.first(quantifier)

def operated(operator):
    return Operated.first(operator)

def tabiter(logic=None, *args, **kw):
    from proof.tableaux import Tableau
    from www.conf import available
    logics = iter(tuple((logic,) if logic else available['logics']))
    return chain.from_iterable(
        (Tableau(logic, arg, **kw).build() for arg in arguments())
        for logic in logics
    )
