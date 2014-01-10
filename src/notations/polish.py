import logic
from logic import operate, arity, quantify, is_constant, is_variable

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
        if sentence.predicate.name in Parser.pnames:
            idx = Parser.pnames[sentence.predicate.name]
            s = idx[0]
            if idx[1] > 0:
                s += idx[1]
        else:
            s = write_item(sentence.predicate, Parser.pchars)
        for param in sentence.parameters:
            if is_constant(param):
                s += write_item(param, Parser.cchars)
            elif is_variable(param):
                s += write_item(param, Parser.vchars)
            else:
                raise Exception(NotImplemented)
    else:
        raise Exception(NotImplemented)
    return s
    
def write_item(item, chars):
    s = chars[item.index]
    if item.subscript > 0:
        s += str(item.subscript)
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
        'B': 'Biconditional',
        'M': 'Possibility',
        'L': 'Necessity'
    }
    
    vchars = ['v', 'x', 'y', 'z']
    cchars = ['m', 'n', 'o', 's']
    qchars = {
        'V': 'Universal',
        'S': 'Existential'
    }
    pchars = ['F', 'G', 'H', 'I', 'J', 'K']
    pnames = {
        'Identity': ['I', 0],
        'Existence': ['J', 0]
    }
    pindex = {
        'I': { 0: 'Identity' },
        'J': { 0: 'Existence' }
    }
    
    def read(self):
        self.assert_current()
        if self.current() in self.ochars:
            operator = self.ochars[self.current()]
            self.advance()
            operands = [self.read() for x in range(arity(operator))]
            return operate(operator, operands)
        if self.current() in self.pchars:
            return self.read_predicate_sentence()
        if self.current() in self.qchars:
            quantifier = self.qchars[self.current()]
            self.advance()
            variable = self.read_variable()
            if variable in list(self.bound_vars):
                raise logic.Parser.ParseError('Cannot rebind variable ' + 
                        write_item(variable, self.vchars) + ' at position ' + str(self.pos))
            self.bound_vars.add(variable)
            sentence = self.read()
            if variable not in list(sentence.variables()):
                raise logic.Parser.ParseError('Unused bound variable ' +
                        write_item(variable, self.vchars) + ' at position ' + str(self.pos))
            self.bound_vars.remove(variable)
            return quantify(quantifier, variable, sentence)
        return self.read_atomic()