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

quantifiers = {'Universal', 'Existential'}

def negate(sentence):
    return Vocabulary.MolecularSentence('Negation', [sentence])

def operate(operator, operands):
    return Vocabulary.MolecularSentence(operator, operands)

def atomic(index, subscript):
    return Vocabulary.AtomicSentence(index, subscript)

def arity(operator):
    return operators[operator]

def predicate(index, subscript, arity):
    return Vocabulary.Predicate(index, subscript, arity)

def predicate_sentence(predicate, parameters):
    return Vocabulary.PredicateSentence(predicate, parameters)
    
def quantify(quantifier, variable, sentence):
    return Vocabulary.QuantifiedSentence(quantifier, variable, sentence)
    
def constant(index, subscript):
    return Vocabulary.Constant(index, subscript)
    
def variable(index, subscript):
    return Vocabulary.Variable(index, subscript)
    
def p_arity(index, subscript):
    return Vocabulary.predicates[index][subscript]
    
def is_predicate(index, subscript):
    return (index in Vocabulary.predicates and subscript in Vocabulary.predicates[index])
    
def is_constant(obj):
    return isinstance(obj, Vocabulary.Constant)

def is_variable(obj):
    return isinstance(obj, Vocabulary.Variable)
    
class argument(object):

    def __init__(self, conclusion=None, premises=[]):
        self.premises = premises
        self.conclusion = conclusion
    
    def __repr__(self):
        return [self.premises, self.conclusion].__repr__()

def tableau(logic, arg):
    return TableauxSystem.Tableau(logic, arg)

class Vocabulary(object):
    
    predicates = {}
    
    class NoSuchPredicateError(Exception):
        pass
    
    class PredicateArityMismatchError(Exception):
        pass
            
    class Predicate(object):
        
        def __init__(self, index, subscript, arity):
            if is_predicate(index, subscript):
                if not p_arity(index, subscript) == arity:
                    raise Vocabulary.PredicateArityMismatchError(
                        'Expecting ' + p_arity(index, subscript) + ' for ' + 
                        str([index, subscript]) + ', got ' + arity + ' instead.'
                    )
            else:
                if index not in Vocabulary.predicates:
                    Vocabulary.predicates[index] = {}
                Vocabulary.predicates[index][subscript] = arity
            self.index = index
            self.subscript = subscript
            self.arity = arity
            
        def __eq__(self, other):
            return self.__dict__ == other.__dict__
    
    class Constant(object):
        
        def __init__(self, index, subscript):
            self.index = index
            self.subscript = subscript
        
        def __eq__(self, other):
            return isinstance(other, Vocabulary.Constant) and self.__dict__ == other.__dict__
    
    class Variable(object):
        
        def __init__(self, index, subscript):
            self.index = index
            self.subscript = subscript
            
        def __eq__(self, other):
            return isinstance(other, Vocabulary.Variable) and self.__dict__ == other.__dict__
                    
    class Sentence(object):
        
        operator = None
        quantifier = None
        predicate = None
        
        def is_sentence(self):
            return isinstance(self, Vocabulary.Sentence)
            
        def is_atomic(self):
            return isinstance(self, Vocabulary.AtomicSentence)

        def is_predicate(self):
            return isinstance(self, Vocabulary.PredicateSentence)
            
        def is_quantified(self):
            return isinstance(self, Vocabulary.QuantifiedSentence)
                    
        def is_molecular(self):
            return isinstance(self, Vocabulary.MolecularSentence)
    
        def substitute(self, constant, variable):
            raise NotImplemented
            
        def constants(self):
            raise NotImplemented
            
        def __eq__(self, other):
            return self.__dict__ == other.__dict__
            
        def __repr__(self):
            from notations import polish
            return polish.write(self)
            
    class AtomicSentence(Sentence):
        
        def __init__(self, index, subscript):
            self.index = index
            self.subscript = subscript
            
        def substitute(self, constant, variable):
            return self
            
        def constants(self):
            return set()
            
    class PredicateSentence(Sentence):
        
        def __init__(self, predicate, parameters):
            if len(parameters) != predicate.arity:
                raise Vocabulary.PredicateArityMismatchError('Expecting ' + p_arity(index, subscript) + ' for ' + 
                str([index, subscript]) + ', got ' + arity + ' instead.')
            self.predicate = predicate
            self.parameters = parameters
        
        def substitute(self, constant, variable):
            params = []
            for param in self.parameters:
                if param == variable:
                    params.append(constant)
                else:
                    params.append(param)
            return predicate_sentence(self.predicate, params)
            
        def constants(self):
            return {param for param in self.parameters if is_constant(param)}
    
    class QuantifiedSentence(Sentence):
        
        def __init__(self, quantifier, variable, sentence):
            self.quantifier = quantifier
            self.variable = variable
            self.sentence = sentence
            
        def substitute(self, constant, variable):
            return self.sentence.substitute(constant, variable)
            
        def constants(self):
            return self.sentence.constants()
                      
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

        def substitute(self, constant, variable):
            return operate(self.operator, [operand.substitute(constant, variable) for operand in self.operands])
            
        def constants(self):
            c = set()
            for operand in self.operands:
                c.update(operand.constants())
            return c
                
                        
class TableauxSystem(object):
    
    class Tableau(object):
        
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
            self.valid = (self.finished and len(self.open_branches()) == 0)

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
            
    class Branch(object):
        
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
        
        def worlds(self):
            return TableauxSystem.get_worlds_on_branch(self)
        
        def new_world(self):
            return TableauxSystem.get_new_world(self)

        def constants(self):
            return TableauxSystem.get_constants_on_branch(self)
            
        def new_constant(self):
            return TableauxSystem.get_new_constant(self)
            
        def __repr__(self):
            return self.nodes.__repr__()
                        
    class Node(object):
        
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
        
    class Rule(object):
        
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

    @staticmethod
    def get_worlds_on_branch(branch):
        worlds = set()
        for node in branch.get_nodes():
            if 'world' in node.props:
                worlds.add(node.props['world'])
            if 'world1' in node.props:
                worlds.add(node.props['world1'])
            if 'world2' in node.props:
                worlds.add(node.props['world2'])
        return worlds

    @staticmethod
    def get_new_world(branch):
        worlds = TableauxSystem.get_worlds_on_branch(branch)
        if not len(worlds):
            return 0
        return max(worlds) + 1
        
    @staticmethod
    def get_constants_on_branch(branch):
        constants = set()
        for node in branch.get_nodes():
            if 'sentence' in node.props:
                constants.update(node.props['sentence'].constants())
        return constants
        
    num_constant_chars = 3
    @staticmethod
    def get_new_constant(branch):
        constants = TableauxSystem.get_constants_on_branch(branch)
        if not len(constants):
            return constant(0, 0)
        index = 0
        subscript = 0
        c = constant(index, subscript)
        while c not in list(constants):
            index += 1
            if index == TableauxSystem.num_constant_chars:
                index = 0
                subscript += 1
            c = constant(index, subscript)
        return c
            
class Parser(object):
    
    class ParseError(Exception):
        pass
    
    class UnboundVariableError(Exception):
        pass
    
    class BoundVariableError(Exception):
        pass
            
    achars = []
    ochars = {}
    cchars = []
    vchars = []
    qchars = {}
    pchars = []
    
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
    
    def assert_current_in(self, collection):
        self.assert_current()
        if not self.current() in collection:
            raise Parser.ParseError('Unexpected character "' + self.current() + '" at position ' + str(self.pos))
            
    def has_next(self, n=1):
        return (len(self.s) > self.pos + n)
            
    def next(self, n=1):
        if self.has_next(n):
            return self.s[self.pos+n]
        return None
        
    def advance(self, n=1):
        self.pos += n  
        self.chomp()
    
    def argument(self, conclusion=None, premises=[]):
        return argument(self.parse(conclusion), [self.parse(s) for s in premises])
    
    def parse(self, string):
        self.bound_vars = set()
        self.s = list(string)
        self.pos = 0
        self.chomp()
        if not self.has_next(0):
            raise Parser.ParseError('Input cannot be empty')
        s = self.read()
        self.chomp()
        if self.has_next(0):
            raise Parser.ParseError('Unexpected character "' + self.current() + '" at position ' + str(self.pos))
        return s
        
    def read_atomic(self):
        self.assert_current_in(self.achars)
        index = self.achars.index(self.current())
        self.advance()
        subscript = self.read_subscript()
        return atomic(index, subscript)
    
    def read_subscript(self):
        sub = ['0']
        while (self.current() and self.current().isdigit()):
            sub.append(self.current())
            self.advance()
        return int(''.join(sub))
        
    def read_variable(self):
        self.assert_current_in(self.vchars)
        index = self.vchars.index(self.current())
        self.advance()
        subscript = self.read_subscript()
        return variable(index, subscript)

    def read_constant(self):
        self.assert_current_in(self.cchars)
        index = self.cchars.index(self.current())
        self.advance()
        subscript = self.read_subscript()
        return constant(index, subscript)
    
    def read_predicate(self):
        self.assert_current_in(self.pchars)
        index = self.pchars.index(self.current())
        self.advance()
        subscript = self.read_subscript()
        if not is_predicate(index, subscript):
            raise Parser.ParseError('Undefined predicate symbol "' + self.current() + '" at position ' + str(self.pos))
        return predicate(index, subscript, p_arity(index, subscript))
            
    def read_predicate_sentence(self):
        predicate = self.read_predicate()
        parameters = []
        while len(parameters) < predicate.arity:
            self.assert_current_in(self.cchars + self.vchars)
            if self.current() in self.cchars:
                parameters.append(self.read_constant())
            else:
                variable = self.read_variable()
                if variable not in list(self.bound_vars):
                    raise Parser.UnboundVariableError(self.vchars[variable.index] + str(variable.subscript) + ' at position ' + str(self.pos))
                parameters.append(variable)
        return predicate_sentence(predicate, parameters)
            
    def read(self):
        return self.read_atomic()