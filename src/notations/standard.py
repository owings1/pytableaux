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
# pytableaux - Standard Notation

import logic
from logic import write_item

name = 'Standard'

def write(sentence):
    if sentence.is_atomic():
        s = write_item(sentence, Parser.achars)
    elif sentence.is_molecular():
        ostr = Parser.ochars.keys()[Parser.ochars.values().index(sentence.operator)]
        if logic.arity(sentence.operator) == 1:
            s = ostr
            s += write(sentence.operand)
        else:
            assert logic.arity(sentence.operator) == 2
            s = Parser.pochars[0]
            s += list(Parser.wschars)[0].join([write(sentence.lhs), ostr, write(sentence.rhs)])
            s += Parser.pcchars[0]
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
    achars = ['A', 'B', 'C', 'D', 'E']

    # operator characters
    ochars = {
        '~': 'Negation',
        '&': 'Conjunction',
		'v': 'Disjunction',
		'>': 'Material Conditional',
		'<': 'Material Biconditional',
		'$': 'Conditional',
		'%': 'Biconditional',
		'P': 'Possibility',
		'N': 'Necessity'
    }

    # variable characters
    vchars = ['v', 'x', 'y', 'z']

    # constant characters
    cchars = ['a', 'b', 'c', 'd']

    # quantifier characters
    qchars = {
        'V' : 'Universal',
        'S' : 'Existential'
    }
    upchars = ['F', 'G', 'H', 'O']
    spchars = ['I', 'J']

    pochars = ['(']
    pcchars = [')']

    def read(self):
        self.assert_current()
        if self.current() in self.ochars:
            operator = self.ochars[self.current()]
            arity = logic.arity(operator)
            # only unary operators can be prefix operators
            if arity != 1:
                raise logic.Parser.ParseError("Unexpected non-prefix operator symbol '{0}' at position {1}".format(self.current(), self.real_pos()))
            self.advance()
            operand = self.read()
            return logic.operate(operator, [operand])

        if self.current() in self.pochars:
            # if we have an open parenthesis, then we demand a binary infix operator sentence.
            # scan ahead to:
            #   - find the corresponding close parenthesis position
            #   - find the binary operator and its position
            operator = None
            operator_pos = None
            depth = 1
            length = 1
            while depth:
                if not self.has_next(length):
                    raise logic.Parser.ParseError('Unterminated open parenthesis at position {0}'.format(self.pos))
                peek = self.next(length)
                if peek in self.pcchars:
                    depth -= 1
                elif peek in self.pochars:
                    depth += 1
                elif peek in self.ochars and logic.arity(self.ochars[peek]) == 2 and depth == 1:
                    if operator != None:
                        raise logic.Parser.ParseError('Unexpected binary operator at position {0}'.format(self.pos + length))
                    operator_pos = self.pos + length
                    operator = self.ochars[peek]
                length += 1
            if length == 1:
                raise logic.Parser.ParseError('Empty parenthetical expression at position {0}'.format(self.pos))
            if operator == None:
                raise logic.Parser.ParseError('Parenthetical expression is missing binary operator at position {0}'.format(self.pos))
            # now we can divide the string into lhs and rhs
            lhs_start = self.pos + 1
            # move past the open paren
            self.advance()
            # read the lhs
            lhs = self.read()
            self.chomp()
            if self.pos != operator_pos:
                raise logic.Parser.ParseError('Invalid left expression start at position {0} and ending at position {1}, proceeds past operator at position {2}'.format(lhs_start, self.pos, operator_pos))
            # move past the operator
            self.advance()
            # read the rhs
            rhs = self.read()
            self.chomp()
            # now we should have a close paren
            self.assert_current_in(self.pcchars)
            # move past the close paren
            self.advance()
            return logic.operate(operator, [lhs, rhs])
        return logic.Parser.read(self)