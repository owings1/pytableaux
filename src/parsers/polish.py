import logic

class Parser(logic.Parser):
    
    achars = ['a', 'b', 'c', 'd', 'e']
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
    
    def read(self):
        self.assert_current()
        if self.current() in self.ochars:
            operator = self.ochars[self.current()]
            self.advance()
            operands = [self.read() for x in range(logic.arity(operator))]
            return logic.operate(operator, operands)
        return self.read_atomic()