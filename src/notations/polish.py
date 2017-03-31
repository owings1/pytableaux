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
# pytableaux - Polish Notation
"""
Polish notation is a fully *prefix* notation, meaning the operators occur before
the operands.
"""
import logic, string

name = 'Polish'

symbol_sets = {
    'default' : logic.Parser.SymbolSet('default', {
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
        'digit' : list(string.digits)
    })
}

class Writer(logic.Vocabulary.Writer):

    symbol_sets = {
        'default' : symbol_sets['default'],
        'html'    : logic.Parser.SymbolSet('html', symbol_sets['default'].m)
    }

    def write_operated(self, sentence, symbol_set = None):
        symset = self.symset(symbol_set)
        return symset.charof('operator', sentence.operator) + ''.join([
            self.write(operand, symbol_set = symbol_set) for operand in sentence.operands
        ])
    
class Parser(logic.Parser):

    symbol_sets = symbol_sets

    def read(self):
        ctype = self.assert_current()
        if ctype == 'operator':
            operator = self.symbol_set.indexof('operator', self.current())
            self.advance()
            operands = [self.read() for x in range(logic.arity(operator))]
            s = logic.operate(operator, operands)
        else:
            s = super(Parser, self).read()
        return s

writer = Writer()
def write(sentence, symbol_set = None):
    return writer.write(sentence, symbol_set = symbol_set)