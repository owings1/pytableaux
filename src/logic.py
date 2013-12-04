operators = {
    'Negation': 1,
    'Conjunction': 2,
    'Disjunction': 2,
    'Material Conditional': 2,
    'Material Biconditional': 2,
    'Conditional': 2,
    'Possibility': 1,
    'Necessity': 1
}

def negate(sentence):
    return Vocabulary.MolecularSentence('Negation', [sentence])

def operate(operator, operands):
    return Vocabulary.MolecularSentence(operator, operands)

def atomic(index, subscript):
    return Vocabulary.AtomicSentence(index, subscript)

def arity(operator):
    return operators[operator]
    
class argument:

    def __init__(self, premises, conclusion):
        self.premises = premises
        self.conclusion = conclusion

def tableau(logic, arg):
    return TableauxSystem.Tableau(logic, arg)
            
class Vocabulary:
    
    class Sentence:
        def is_sentence(self):
            return self.is_atomic() or self.is_molecular()
            
        def is_atomic(self):
            return (hasattr(self, 'index') and hasattr(self, 'subscript'))

        def is_molecular(self):
            return (hasattr(self, 'operator') and hasattr(self, 'operands'))
            
    class AtomicSentence(Sentence):
        
        def __init__(self, index, subscript):
            self.index = index
            self.subscript = subscript
            self.operator = None
            
        def __eq__(self, other):
            assert Vocabulary.Sentence.is_sentence(other)
            return (other.is_atomic() and
                    self.index == other.index and
                    self.subscript == other.subscript)
        
    class MolecularSentence(Sentence):
        
        def __init__(self, operator, operands):
            assert operator in operators
            assert len(operands) == operators[operator]
            self.operator = operator
            self.operands = operands
            
        def __eq__(self, other):
            assert Vocabulary.Sentence.is_sentence(other)
            return (other.is_molecular() and
                    self.operator == other.operator and
                    self.operands == other.operands)

class TableauxSystem:
    
    class Tableau:
        
        def __init__(self, logic, argument):
            self.logic = logic
            self.argument = argument
            self.branches = set()
            self.finished = False
            self.rules = []
            for Rule in logic.TableauxRules.rules:
                self.rules.append(Rule(self))
            
        def open_branches(self):
            return {branch for branch in self.branches if not branch.closed}
            
        def branch(self):
            branch = TableauxSystem.Branch()
            self.branches.add(branch)
            return branch
            
        def build_trunk(self):
            return self.logic.TableauxSystem.build_trunk(self)
            
        def step(self):
            if self.finished:
                return False
            for rule in self.rules:
                if rule.applies():
                    rule.apply()
                    return True
            self.finished = True
        
        def build(self):
            self.build_trunk()
            while not self.finished:
                self.step()
            return self
        
        def valid(self):
            return (self.finished and len(self.open_branches()) == 0)
            
    class Branch:
        
        def __init__(self):
            self.nodes = []
            self.ticked_nodes = set()
            self.closed = False

        def has(self, props, ticked=None):
            for node in self.get_nodes(ticked=ticked):
                if node.has_props(props):
                    return True
            return False
 
        def add(self, node):
            if not isinstance(node, TableauxSystem.Node):
                node = TableauxSystem.Node(props=node)
            self.nodes.append(node)
            return self
            
        def tick(self, node):
            self.ticked_nodes.add(node)
            return self
        
        def close(self):
            self.closed = True
            return self
            
        def get_nodes(self, ticked=None):
            if ticked == None:
                return self.nodes
            return [node for node in self.nodes if ticked == (node in self.ticked_nodes)]
        
        def branch(self, node, tableau):
            branch = TableauxSystem.Branch()
            branch.nodes = list(self.nodes)
            branch.ticked_nodes = set(self.ticked_nodes)
            branch.add(node)
            tableau.branches.add(branch)
            return branch
                        
    class Node:
        
        def __init__(self, props={}):
            self.props = props
        
        def has_props(self, props):
            for prop in props:
                if prop not in self.props or not props[prop] == self.props[prop]:
                    return False
            return True

    class Rule:
        
        def __init__(self, tableau):
            self.tableau = tableau
            
        def applies(self):
            return False
            
        def apply(self):
            pass

    class BranchRule(Rule):
        
        def applies(self):
            for branch in self.tableau.open_branches():
                if self.applies_to_branch(branch):
                    return True
            return False
            
        def apply(self):
            for branch in self.tableau.open_branches():
                if self.applies_to_branch(branch):
                    return self.apply_to_branch(branch)
                    
        def applies_to_branch(self, branch):
            return False
            
        def apply_to_branch(self, branch):
            pass

    class NodeRule(BranchRule):

        def applies_to_branch(self, branch):
            for node in branch.get_nodes(ticked=False):
                if self.applies_to_node(node, branch):
                    return True
            return False

        def apply_to_branch(self, branch):
            for node in branch.get_nodes(ticked=False):
                if self.applies_to_node(node, branch):
                    return self.apply_to_node(node, branch)

        def applies_to_node(self, node, branch):
            return False

        def apply_to_node(self, node, branch):
            pass

    class ClosureRule(BranchRule):

        def apply_to_branch(self, branch):
            branch.close()

class Parser:
    
    class ParseError(Exception):
        pass
    Error = ParseError
    
    achars = []
    ochars = {}
    wschars = set([' '])
        
    def chomp(self):
        while (self.has_next(0) and self.current() in self.wschars):
            self.pos += 1
    
    def current(self):
        if self.has_next(0):
            return self.s[self.pos]
        return None
    
    def assert_current(self):
        if not self.has_next(0):
            raise Error('Unexpected end of input at position ' + str(self.real_pos()))
    
    def real_pos(self):
        return self.pos + self.parent_pos
        
    def has_next(self, n=1):
        return (len(self.s) > self.pos + n)
            
    def next(self, n=1):
        if self.has_next(n):
            return self.s[self.pos+n]
        return None
        
    def advance(self, n=1):
        self.pos += n  
        self.chomp()
    
    def argument(self, premises, conclusion):
        return argument([self.parse(s) for s in premises], self.parse(conclusion))
    
    def parse(self, string, parent_pos=0):
        self.s = list(string)
        self.pos = 0
        self.parent_pos = parent_pos
        self.chomp()
        s = self.read()
        self.chomp()
        if self.has_next(0):
            raise Error('Unexpected character: "' + self.current() + '" at position ' + str(self.real_pos() + 1))
        return s
        
    def read_atomic(self):
        self.assert_current()
        if self.current() in self.achars:
            achar = self.current()
            self.advance()
            sub = ['0']
            while (self.current() and self.current().isdigit()):
                sub.append(self.current())
                self.advance()
            return atomic(self.achars.index(achar), int(''.join(sub)))
        raise Error('Unexpected character: "' + self.current() + '" at position ' + str(self.real_pos()))
    
    def read(self):
        return self.read_atomic()
        
def main():
    test()
    
def test():
    import logics.cpl, parsers.polish
    logics = [logics.cpl]
    parser = parsers.polish.Parser()
    
    for logic in logics:
        print logic.name
        print '  validities'
        test_arguments(logic, logic.example_validities(), True, parser)
        print '  invalidities'
        test_arguments(logic, logic.example_invalidities(), False, parser)
        

def test_arguments(logic, args, valid, parser):
    for name in args:
        print '    ', name, '...',
        test_argument(logic, args[name][0], args[name][1], valid, parser)
        print 'pass'

def test_argument(logic, premises, conclusion, valid, parser):
    assert valid == tableau(logic, parser.argument(premises, conclusion)).build().valid()
    
if  __name__ =='__main__':main()