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