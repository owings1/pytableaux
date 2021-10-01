default_notation = 'polish'

# name : arity
operators = {
    'Assertion'              : 1,
    'Negation'               : 1,
    'Conjunction'            : 2,
    'Disjunction'            : 2,
    'Material Conditional'   : 2,
    'Material Biconditional' : 2,
    'Conditional'            : 2,
    'Biconditional'          : 2,
    'Possibility'            : 1,
    'Necessity'              : 1,
}

# Default display ordering
operators_list = [
    'Assertion'              ,
    'Negation'               ,
    'Conjunction'            ,
    'Disjunction'            ,
    'Material Conditional'   ,
    'Material Biconditional' ,
    'Conditional'            ,
    'Biconditional'          ,
    'Possibility'            ,
    'Necessity'              ,
]

quantifiers_list = [
    'Universal'  ,
    'Existential',
]

system_predicates_list  = [
    'Identity' ,
    'Existence',
]

system_predicates_index = {
    # Negative indexes for system predicates. Value is subscript : name.
    -1 : { 0 : 'Identity'  },
    -2 : { 0 : 'Existence' },
}

# The number of symbols is fixed to allow multiple notations.
num_var_symbols       = 4
num_const_symbols     = 4
num_atomic_symbols    = 5
num_predicate_symbols = 4

symbols_data = {
    'polish' : {
        'ascii' : {
            'atomic'   : ['a', 'b', 'c', 'd', 'e'],
            'operator' : {
                'Assertion'              : 'T',
                'Negation'               : 'N',
                'Conjunction'            : 'K',
                'Disjunction'            : 'A',
                'Material Conditional'   : 'C',
                'Material Biconditional' : 'E',
                'Conditional'            : 'U',
                'Biconditional'          : 'B',
                'Possibility'            : 'M',
                'Necessity'              : 'L',
            },
            'variable'   : ['x', 'y', 'z', 'v'],
            'constant'   : ['m', 'n', 'o', 's'],
            'quantifier' : {
                'Universal'   : 'V',
                'Existential' : 'S',
            },
            'system_predicate'  : {
                'Identity'  : 'I',
                'Existence' : 'J',
            },
            'user_predicate' : ['F', 'G', 'H', 'O'],
            'whitespace'     : [' '],
            'digit' : list('0123456789'),
        },
    },
    'standard': {
        'ascii': {
            'atomic' : ['A', 'B', 'C', 'D', 'E'],
            'operator' : {
                'Assertion'              :  '*',
                'Negation'               :  '~',
                'Conjunction'            :  '&',
                'Disjunction'            :  'V',
                'Material Conditional'   :  '>',
                'Material Biconditional' :  '<',
                'Conditional'            :  '$',
                'Biconditional'          :  '%',
                'Possibility'            :  'P',
                'Necessity'              :  'N',
            },
            'variable' : ['x', 'y', 'z', 'v'],
            'constant' : ['a', 'b', 'c', 'd'],
            'quantifier' : {
                'Universal'   : 'L',
                'Existential' : 'X',
            },
            'system_predicate'  : {
                'Identity'  : '=',
                'Existence' : '!',
            },
            'user_predicate'  : ['F', 'G', 'H', 'O'],
            'paren_open'      : ['('],
            'paren_close'     : [')'],
            'whitespace'      : [' '],
            'digit'           : list('0123456789'),
        },
        'html': {
            'atomic'   : ['A', 'B', 'C', 'D', 'E'],
            'operator' : {
                'Assertion'              : '&deg;'   ,
                'Negation'               : '&not;'   ,
                'Conjunction'            : '&and;'   ,
                'Disjunction'            : '&or;'    ,
                'Material Conditional'   : '&sup;'   ,
                'Material Biconditional' : '&equiv;' ,
                'Conditional'            : '&rarr;'  ,
                'Biconditional'          : '&harr;'  ,
                'Possibility'            : '&#9671;' ,
                'Necessity'              : '&#9723;' ,
            },
            'variable'   : ['x', 'y', 'z', 'v'],
            'constant'   : ['a', 'b', 'c', 'd'],
            'quantifier' : {
                'Universal'   : '&forall;' ,
                'Existential' : '&exist;'  ,
            },
            'system_predicate'  : {
                'Identity'  : '=',
                'Existence' : 'E!',
                'NegatedIdentity' : '&ne;',
            },
            'user_predicate'  : ['F', 'G', 'H', 'O'],
            'paren_open'      : ['('],
            'paren_close'     : [')'],
            'whitespace'      : [' '],
            'digit'           : list('0123456789'),
        }
    }
}

for notn in symbols_data:
    symbols_data[notn]['default'] = symbols_data[notn]['ascii']