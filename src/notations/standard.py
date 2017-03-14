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

class Parser(logic.Parser):
    
    achars = ['A', 'B', 'C', 'D', 'E']
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

    vchars = ['v', 'x', 'y', 'z']
    cchars = ['a', 'b', 'c', 'd']
    qchars = {
        'V' : 'Universal',
        'S' : 'Existential'
    }
    upchars = ['F', 'G', 'H', 'O']
    spchars = ['I', 'J']

    pochars = ['(']
    pcchars = [')']
    sepchars = [',']

    def read(self):
        self.assert_current()
        if self.current() in self.achars:
            pass
        elif self.current() in self.pochars:
            depth = 1
            start = self.pos
            length = 1
            while depth:
                if not self.has_next(length):
                    raise logic.Parser.ParseError('Unterminated open parenthesis at position ' + str(self.real_pos()))
                if self.next(length) in self.pcchars:
                    if length == 1:
                        raise logic.Parser.ParseError('Empty parenthetical expression at position ' + str(self.real_pos()))
                    depth -= 1
                length += 1


            pass
        elif self.current() in self.ochars:
            operator = self.ochars[self.current()]
            self.advance()
            arity = logic.operators[operator]
            operands = []
            for x in range(arity):
                operands.append(self.read())
                if len(operands) < arity:
                    if self.current() not in self.sepchars:
                        raise logic.Parser.ParseError('Expecting separator character "' + self.sepchars[0] + '" at position ' + str(self.real_pos()))
                    self.advance()
            return logic.operate(operator, operands)
        return logic.Parser.read(self)