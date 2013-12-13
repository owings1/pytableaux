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
    
    def __repr__(self):
        return [self.premises, self.conclusion].__repr__()

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
    
        def __repr__(self):
            from notations import polish
            return polish.write(self)
            
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
            assert len(operands) == arity(operator)
            self.operator = operator
            self.operands = operands
            if len(operands) == 1:
                self.operand = operands[0]
            elif len(operands) > 1:
                self.lhs = operands[0]
                self.rhs = operands[-1]
            
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
            self.rules = [Rule(self) for Rule in logic.TableauxRules.rules]
            self.history = []
            
        def open_branches(self):
            return {branch for branch in self.branches if not branch.closed}
            
        def branch(self, other_branch=None):
            if not other_branch:
                branch = TableauxSystem.Branch()
            else:
                branch = other_branch.copy()
                self.branches.discard(other_branch)
            self.branches.add(branch)
            return branch
            
        def build_trunk(self):
            return self.logic.TableauxSystem.build_trunk(self, self.argument)
            
        def step(self):
            if self.finished:
                return False
            for rule in self.rules:
                target = rule.applies()
                if target:
                    rule.apply(target)
                    application = { 'rule': rule, 'target': target }
                    self.history.append(application)
                    return application
            self.finish()
            return False
        
        def build(self):
            self.build_trunk()
            while not self.finished:
                self.step()
            return self
        
        def finish(self):
            self.finished = True
            self.tree = self.structure(self.branches)
            
        def valid(self):
            return (self.finished and len(self.open_branches()) == 0)
            
        def structure(self, branches, depth=0):
            structure = { 'nodes': [], 'children': [], 'closed': False }
            while True:
                B = {branch for branch in branches if len(branch.nodes) > depth}
                distinct_nodes = {branch.nodes[depth] for branch in B}
                if len(distinct_nodes) == 1:
                    structure['nodes'].append(list(B)[0].nodes[depth])
                    depth += 1
                    continue
                break
            for node in distinct_nodes:
                child_branches = {branch for branch in branches if branch.nodes[depth] == node}
                structure['children'].append(self.structure(child_branches, depth))
            if len(branches) == 1:
                structure['closed'] = list(branches)[0].closed
            return structure
            
        def __repr__(self):
            return {
                'argument': self.argument,
                'branches': len(branches),
                'rules_applied': len(history),
                'finished': self.finished
            }.__repr__()
            
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
        
        def update(self, nodes):
            for node in nodes:
                self.add(node)
            return self
            
        def tick(self, node):
            self.ticked_nodes.add(node)
            node.ticked = True
            return self
        
        def close(self):
            self.closed = True
            return self
            
        def get_nodes(self, ticked=None):
            if ticked == None:
                return self.nodes
            return [node for node in self.nodes if ticked == (node in self.ticked_nodes)]
        
        def copy(self):
            branch = TableauxSystem.Branch()
            branch.nodes = list(self.nodes)
            branch.ticked_nodes = set(self.ticked_nodes)
            return branch
        
        def __repr__(self):
            return self.nodes.__repr__()
                        
    class Node:
        
        def __init__(self, props={}):
            self.props = props
            self.ticked = False
        
        def has_props(self, props):
            for prop in props:
                if prop not in self.props or not props[prop] == self.props[prop]:
                    return False
            return True
        
        def __repr__(self):
            return self.__dict__.__repr__()
        
    class Rule:
        
        def __init__(self, tableau):
            self.tableau = tableau
            
        def applies(self):
            return False
            
        def apply(self, target):
            pass
        
        def __repr__(self):
            return self.__class__.__name__

    class BranchRule(Rule):
        
        def applies(self):
            for branch in self.tableau.open_branches():
                target = self.applies_to_branch(branch)
                if target:
                    return target
            return False
                    
        def applies_to_branch(self, branch):
            return False

    class NodeRule(BranchRule):

        def applies(self):
            for branch in self.tableau.open_branches():
                for node in branch.get_nodes(ticked=False):
                    if self.applies_to_node(node, branch):
                        return { 'node': node, 'branch': branch }
            
        def apply(self, target):
            return self.apply_to_node(target['node'], target['branch'])

        def applies_to_node(self, node, branch):
            raise NotImplemented

        def apply_to_node(self, node, branch):
            raise NotImplemented

    class ClosureRule(BranchRule):

        def applies_to_branch(self, branch):
            raise NotImplemented
        
        def apply(self, branch):
            branch.close()

class Parser:
    
    class ParseError(Exception):
        pass
    
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
            raise Parser.ParseError('Unexpected end of input at position ' + str(self.pos))
        
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
    
    def parse(self, string):
        self.s = list(string)
        self.pos = 0
        self.chomp()
        s = self.read()
        self.chomp()
        if self.has_next(0):
            raise Parser.ParseError('Unexpected character: "' + self.current() + '" at position ' + str(self.pos + 1))
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
        raise Parser.ParseError('Unexpected character: "' + self.current() + '" at position ' + str(self.pos))
    
    def read(self):
        return self.read_atomic()