# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
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

import logic
from notations import polish

# polish notation
args = {
    'Addition'                         : [[ 'a' ], 'Aab'   ],
    'Affirming a Disjunct 1'           : [[ 'Aab', 'a'  ], 'b'  ],
    'Affirming a Disjunct 2'           : [[ 'Aab', 'a'  ], 'Nb' ],
    'Affirming the Consequent'         : [[ 'Cab', 'b'  ], 'a'  ],
    'Biconditional Elimination 1'      : [[ 'Eab', 'a'  ], 'b'  ],
    'Biconditional Elimination 2'      : [[ 'Eab', 'Na' ], 'Nb' ],
    'Biconditional Identity'           : 'Baa',
    'Conditional Contraction'          : [[ 'UaUab' ], 'Uab'   ],
    'Conditional Equivalence'          : [[ 'Uab'   ], 'Uba'  ],
    'Conditional Identity'             : 'Uaa',
    'Conditional Modus Ponens'         : [[ 'Uab', 'a'  ], 'b'  ],
    'Conditional Modus Tollens'        : [[ 'Uab', 'Nb' ], 'Na' ],
    'DeMorgan 1'                       : [[ 'NAab'  ], 'KNaNb' ],
    'DeMorgan 2'                       : [[ 'NKab'  ], 'ANaNb' ],
    'DeMorgan 3'                       : [[ 'KNaNb' ], 'NAab'  ],
    'DeMorgan 4'                       : [[ 'ANaNb' ], 'NKab'  ],
    'Denying the Antecedent'           : [[ 'Cab', 'Na' ], 'b'  ],
    'Disjunctive Syllogism'            : [[ 'Aab', 'Nb' ], 'a'  ],
    'Existential from Universal'       : [[ 'SxFx' ], 'VxFx' ],
    'Existential Syllogism'            : [[ 'VxCFxGx', 'Fn'  ],  'Gn'],
    'Extracting a Disjunct 1'          : [[ 'Aab'  ], 'b'    ],
    'Extracting a Disjunct 2'          : [[ 'AaNb' ], 'Na'   ],
    'Extracting the Antecedent'        : [[ 'Cab'  ], 'a'    ],
    'Extracting the Consequent'        : [[ 'Cab'  ], 'b'    ],
    'Law of Excluded Middle'           : 'AaNa',
    'Law of Non-contradiction'         : [[ 'KaNa' ], 'b'  ],
    'Material Biconditional Identity'  : 'Eaa',
    'Material Contraction'             : [[ 'CaCab' ], 'Cab'   ],
    'Material Identity'                : 'Caa',
    'Material Modus Ponens'            : [[ 'Cab', 'a'  ], 'b'  ],
    'Material Modus Tollens'           : [[ 'Cab', 'Nb' ], 'Na' ],
    'Modal Platitude 1'                : [[ 'Ma'   ], 'Ma'   ],
    'Modal Platitude 2'                : [[ 'La'   ], 'La'   ],
    'Modal Platitude 3'                : [[ 'LMa'  ], 'LMa'  ],
    'Modal Transformation 1'           : [[ 'La'   ], 'NMNa' ],
    'Modal Transformation 2'           : [[ 'NMNa' ], 'La'   ],
    'Modal Transformation 3'           : [[ 'NLa'  ], 'MNa'  ],
    'Modal Transformation 4'           : [[ 'MNa'  ], 'NLa'  ],
    'Necessity Distribution'           : 'CLCabCLaLb',
    'Necessity Elimination'            : [[ 'La'  ], 'a' ],
    'NP Collapse 1'                    : [[ 'LMa' ], 'Ma'],
    'Possibility Addition'             : [[ 'a'   ], 'Ma'],
    'Possibility Distribution'         : [[ 'KMaMb' ], 'MKab'],
    'Pseudo Contraction'               : 'CCaCabCab',
    'Reflexive Inference 1'            : 'CLaa',
    'S4 Conditional Inference 1'       : 'ULaLLa',
    'S4 Inference 1'                   : 'CLaLLa',
    'S4 Material Inference 1'          : 'CLaLLa',
    'S5 Conditional Inference 1'       : 'UaLMa',
    'S5 Material Inference 1'          : 'CaLMa',
    'Serial Inference 1'               : 'CLaMa',
    'Simplification'                   : [[ 'Kab' ], 'a' ],
    'Syllogism'                        : [[ 'VxCFxGx', 'VxCGxHx' ], 'VxCFxHx'],
    'Triviality 1'                     : 'a',
    'Triviality 2'                     : [[ 'a' ], 'b' ],
    'Universal Predicate Syllogism'    : [[ 'VxVyCO0xyO1xy', 'O0nm'], 'O1nm'],
}

args_list = sorted(args.keys())

# Test vocabulary predicate data
test_pred_data = [
    ['is F', 0, 0, 1],
    ['is G', 1, 0, 1],
    ['is H', 2, 0, 1],
    ['Os'  , 3, 0, 2],
    ['O1s' , 3, 1, 2]
]

vocabulary = logic.Vocabulary(test_pred_data)
parser = polish.Parser(vocabulary)

def argument(name):
    info = args[name]
    if isinstance(info, list):
        premises = info[0]
        conclusion = info[1]
    else:
        premises = []
        conclusion = info
    return parser.argument(conclusion=conclusion, premises=premises, title=name)

def arguments(names=None):
    if names == None:
        names = args_list
    return [argument(name) for name in names]