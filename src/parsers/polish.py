import logic

class Parser(logic.Parser):
    
    ochars = {
        'N': 'Negation',
        'K': 'Conjunction',
		'A': 'Disjunction',
		'C': 'Material Conditional',
		'E': 'Material Biconditional',
		'U': 'Conditional',
		'M': 'Possibility',
		'L': 'Necessity'
    }
    
    achars = ['a', 'b', 'c', 'd', 'e']
    
    def read(self):
        self.assert_current()
        if self.current() in self.ochars:
            operator = self.ochars[self.current()]
            self.advance()
            operands = []
            for x in range(logic.operators[operator]):
                operands.append(self.read())
            return logic.operate(operator, operands)
        return logic.Parser.read(self)