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
    'default' : logic.Parser.SymbolSet({
        'atomic'   : ['a', 'b', 'c', 'd', 'e'],
        'operator' : {
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
        'variable'   : ['v', 'x', 'y', 'z'],
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

def write(sentence, symbol_set = None):
    if symbol_set == None:
        symbol_set = symbol_sets['default']
    if isinstance(symbol_set, str):
        symbol_set = symbol_sets[symbol_set]
    if sentence.is_atomic():
        s = symbol_set.charof('atomic', sentence.index, subscript = sentence.subscript)
    elif sentence.is_molecular():
        s = symbol_set.charof('operator', sentence.operator)
        s += ''.join([write(operand, symbol_set = symbol_set) for operand in sentence.operands])
    elif sentence.is_quantified():
        s = symbol_set.charof('quantifier', sentence.quantifier)
        s += symbol_set.charof('variable', sentence.variable.index, subscript = sentence.variable.subscript)
        s += write(sentence.sentence, symbol_set = symbol_set)
    elif sentence.is_predicated():
        if sentence.predicate.name in logic.system_predicates:
            s = symbol_set.charof('system_predicate', sentence.predicate.name, subscript = sentence.predicate.subscript)
        else:
            s = symbol_set.charof('user_predicate', sentence.predicate.index, subscript = sentence.predicate.subscript)
        for param in sentence.parameters:
            if param.is_constant():
                s += symbol_set.charof('constant', param.index, subscript = param.subscript)
            elif param.is_variable():
                s += symbol_set.charof('variable', param.index, subscript = param.subscript)
            else:
                raise Exception(NotImplemented)
    else:
        raise Exception(NotImplemented)
    return s
    
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