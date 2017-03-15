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

import logic
from logic import write_item

name = 'Polish'

def write(sentence):
    if sentence.is_atomic():
        s = write_item(sentence, Parser.achars)
    elif sentence.is_molecular():
        s = Parser.ochars.keys()[Parser.ochars.values().index(sentence.operator)]
        for operand in sentence.operands:
            s += write(operand)
    elif sentence.is_quantified():
        s = Parser.qchars.keys()[Parser.qchars.values().index(sentence.quantifier)]
        s += write_item(sentence.variable, Parser.vchars)
        s += write(sentence.sentence)
    elif sentence.is_predicate():
        if sentence.predicate.name in logic.system_predicates:
            s = write_item(sentence.predicate, Parser.spchars)
        else:
            s = write_item(sentence.predicate, Parser.upchars)
        for param in sentence.parameters:
            if logic.is_constant(param):
                s += write_item(param, Parser.cchars)
            elif logic.is_variable(param):
                s += write_item(param, Parser.vchars)
            else:
                raise Exception(NotImplemented)
    else:
        raise Exception(NotImplemented)
    return s
    
class Parser(logic.Parser):

    # atomic sentence characters
    achars = ['a', 'b', 'c', 'd', 'e']

    # operator characters
    ochars = {
        'N' : 'Negation',
        'K' : 'Conjunction',
        'A' : 'Disjunction',
        'C' : 'Material Conditional',
        'E' : 'Material Biconditional',
        'U' : 'Conditional',
        'B' : 'Biconditional',
        'M' : 'Possibility',
        'L' : 'Necessity'
    }

    # variable characters
    vchars = ['v', 'x', 'y', 'z']

    # constant characters
    cchars = ['m', 'n', 'o', 's']

    # quantifier characters
    qchars = {
        'V' : 'Universal',
        'S' : 'Existential'
    }

    # user predicate characters
    upchars = ['F', 'G', 'H', 'O']

    # system predicate characters
    spchars = ['I', 'J']

    def read(self):
        self.assert_current()
        if self.current() in self.ochars:
            operator = self.ochars[self.current()]
            self.advance()
            operands = [self.read() for x in range(logic.arity(operator))]
            return logic.operate(operator, operands)
        return logic.Parser.read(self)