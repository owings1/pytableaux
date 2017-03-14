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
		'P': 'Possibility',
		'N': 'Necessity'
    }
    
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
                    raise Error('Unterminated open parenthesis at position ' + str(self.real_pos()))
                
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
                        raise Error('Expecting separator character "' + self.sepchars[0] + '" at position ' + str(self.real_pos()))
                    self.advance()
            return logic.operate(operator, operands)
        return logic.Parser.read(self)