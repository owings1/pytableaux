import logic
from logic import operate, arity

def write(sentence):
    if sentence.is_atomic():
        s = Parser.achars[sentence.index]
        if sentence.subscript > 0:
            s += str(sentence.subscript)
    elif sentence.is_molecular():
        s = Parser.ochars.keys()[Parser.ochars.values().index(sentence.operator)]
        for operand in sentence.operands:
            s += write(operand)
    else:
        raise NotImplemented
    return s
    
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
            operands = [self.read() for x in range(arity(operator))]
            return operate(operator, operands)
        return self.read_atomic()