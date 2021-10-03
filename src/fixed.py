from os import path


__version__ = '2.0.0'

version_info = __version__.split('.')

copyright = '2014-2021, Doug Owings. Released under the GNU Affero General Public License v3 or later'
source_href = 'https://github.com/owings1/pytableaux'
issues_href = 'https://github.com/owings1/pytableaux/issues'
package_dir = path.dirname(path.abspath(__file__))

# compatibility
version = __version__

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

quantifiers = set(quantifiers_list)

system_predicates_list  = [
    'Identity' ,
    'Existence',
]

system_predicates_index = {
    # Negative indexes for system predicates. Value is subscript : name.
    -1 : { 0 : 'Identity'  },
    -2 : { 0 : 'Existence' },
    # Also tuples
    (-1, 0): 'Identity',
    (-2, 0): 'Existence',
}

# The number of symbols is fixed to allow multiple notations.
num_var_symbols       = 4
num_const_symbols     = 4
num_atomic_symbols    = 5
num_predicate_symbols = 4

default_notation = 'polish'
parser_names = ['standard', 'polish']
lexwriter_names = ['standard', 'polish']
lexwriter_encodings = ['html', 'ascii']
tabwriter_names = ['html', 'text']
symbols_data = {
    'polish.ascii' : {
        'name'    : 'polish.ascii',
        'encoding': 'ascii',
        'parse'   : True,
        'lexicals' : {
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
    'standard.ascii': {
        'name'    : 'standard.ascii',
        'encoding': 'ascii',
        'parse'   : True,
        'lexicals': {
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
    },
    'standard.html': {
        'name'    : 'standard.html',
        'encoding': 'html',
        'parse'   : False,
        'lexicals': {
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
        },
    },
}
symbols_data['polish.html'] = symbols_data['polish.ascii']
