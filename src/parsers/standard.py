import logic

class Parser(logic.Parser):
    
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
    
    achars = ['A', 'B', 'C', 'D', 'E']
    
    pochars = ['(']
    pcchars = [')']
    
    sepchars = [',']
    
    def read(self):
        self.assert_current()
        if self.current() in self.ochars:
            operator = self.ochars[self.current()]
            self.advance()
            arity = logic.operators[operator]
            operands = []
            for x in range(arity):
                operands.append(self.read())
                if len(operands) < arity:
                    self.advance()
                    if self.current() not in self.sepchars:
                        raise Exception('Expecting "' + self.sepchars[0] + '" at position ' + str(self.pos))
                    
            return logic.operate(operator, operands)
        return logic.Parser.read(self)