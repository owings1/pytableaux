operators = {
    'Negation': 1,
    'Conjunction': 2,
    'Disjunction': 2,
    'Material Conditional': 2,
    'Material Biconditional': 2,
    'Conditional': 2,
    'Biconditional': 2,
    'Possibility': 1,
    'Necessity': 1
}

operators_list = ['Negation', 'Conjunction', 'Disjunction', 'Material Conditional', 'Material Biconditional',
                  'Conditional', 'Biconditional', 'Possibility', 'Necessity']
                  
conditional_operators = {'Conditional', 'Material Conditional'}
biconditional_operators = {'Biconditional', 'Material Biconditional'}
modal_operators = {'Possibility', 'Necessity'}

quantifiers = ['Universal', 'Existential']

system_predicates = {
    'Identity': 2,
    'Existence': 1
}
system_predicates_list = ['Identity', 'Existence']
num_user_predicate_symbols = 4

def negate(sentence):
    return Vocabulary.MolecularSentence('Negation', [sentence])

def operate(operator, operands):
    return Vocabulary.MolecularSentence(operator, operands)

def atomic(index, subscript):
    return Vocabulary.AtomicSentence(index, subscript)

def arity(operator):
    return operators[operator]

def declare_predicate(name, index, subscript, arity):
    return Vocabulary.declare_predicate(name, index, subscript, arity)
    
def get_predicate(name):
    return Vocabulary.get_predicate(name=name)

def predicate_sentence(predicate, parameters):
    return Vocabulary.PredicateSentence(predicate, parameters)
    
def quantify(quantifier, variable, sentence):
    return Vocabulary.QuantifiedSentence(quantifier, variable, sentence)
    
def constant(index, subscript):
    return Vocabulary.Constant(index, subscript)
    
def variable(index, subscript):
    return Vocabulary.Variable(index, subscript)
    
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
    
    class Predicate(object):
        
        def __init__(self, name, index, subscript, arity):
            self.name = name
            self.index = index
            self.subscript = subscript
            self.arity = arity

    predicates = {}
    for name in system_predicates:
        predicates[name] = Predicate(name, None, None, system_predicates[name])
    predicates_list = list(system_predicates_list)
    _predicates_index = {}
    
    class PredicateError(Exception):
        pass
        
    class NoSuchPredicateError(PredicateError):
        pass
            
    class PredicateArityMismatchError(PredicateError):
        pass
        
    class PredicateIndexMismatchError(PredicateError):
        pass
    
    @staticmethod        
    def get_predicate(name=None, index=None, subscript=None):
        if name != None:
            if name not in Vocabulary.predicates:
                raise Vocabulary.NoSuchPredicateError(name)
            return Vocabulary.predicates[name]
        if index != None and subscript != None:
            idx = str([index, subscript])
            if idx not in Vocabulary._predicates_index:
                raise Vocabulary.NoSuchPredicateError(idx)
            return Vocabulary._predicates_index[idx]
        raise Exception()

    @staticmethod
    def declare_predicate(name, index, subscript, arity):
        try:
            if index != None and subscript != None:
                try:
                    predicate = Vocabulary.get_predicate(index=index, subscript=subscript)
                    if predicate.name != name:
                        raise Vocabulary.PredicateIndexMismatchError(predicate.name + ' is already using ' + str([index, subscript]))
                except Vocabulary.NoSuchPredicateError:
                    pass
            predicate = Vocabulary.get_predicate(name=name)
            if predicate.arity != arity:
                raise Vocabulary.PredicateArityMismatchError(name + ' already declared with arity ' + 
                    str(predicate.arity) + ' not ' + str(arity))
        except Vocabulary.NoSuchPredicateError:
            predicate = Vocabulary.Predicate(name, index, subscript, arity)
            Vocabulary.predicates[name] = predicate
            Vocabulary.predicates_list.append(name)
            if index != None and subscript != None:
                Vocabulary._predicates_index[str([index, subscript])] = predicate
        return predicate

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
            raise Exception(NotImplemented)
            
        def constants(self):
            raise Exception(NotImplemented)
            
        def variables(self):
            raise Exception(NotImplemented)
            
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
            
        def variables(self):
            return set()
            
    class PredicateSentence(Sentence):
        
        def __init__(self, predicate, parameters):
            if len(parameters) != predicate.arity:
                raise Vocabulary.PredicateArityMismatchError('Expecting ' + predicate.arity + ' parameters for predicate ' + 
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
            
        def variables(self):
            return {param for param in self.parameters if is_variable(param)}
    
    class QuantifiedSentence(Sentence):
        
        def __init__(self, quantifier, variable, sentence):
            self.quantifier = quantifier
            self.variable = variable
            self.sentence = sentence
            
        def substitute(self, constant, variable):
            return self.sentence.substitute(constant, variable)
            
        def constants(self):
            return self.sentence.constants()
            
        def variables(self):
            return self.sentence.variables()
                      
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
            
        def variables(self):
            v = set()
            for operand in self.operands:
                v.update(operand.variables())
            return v

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
                'branches': len(self.branches),
                'rules_applied': len(self.history),
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
            
    class ClosureRule(BranchRule):

        def applies_to_branch(self, branch):
            raise Exception(NotImplemented)

        def apply(self, branch):
            branch.close()
            
    class NodeRule(BranchRule):

        def applies(self):
            for branch in self.tableau.open_branches():
                for node in branch.get_nodes(ticked=False):
                    if self.applies_to_node(node, branch):
                        return { 'node': node, 'branch': branch }
            
        def apply(self, target):
            return self.apply_to_node(target['node'], target['branch'])

        def applies_to_node(self, node, branch):
            raise Exception(NotImplemented)

        def apply_to_node(self, node, branch):
            raise Exception(NotImplemented)
        
    class OperatorRule(NodeRule):
        
        operator = None
        
        def applies_to_node(self, node, branch):
            return (self.operator != None and 'sentence' in node.props and 
                    node.props['sentence'].operator == self.operator)
    
    class DoubleOperatorRule(NodeRule):
        
        operators = None
        
        def applies_to_node(self, node, branch):
            return (self.operators != None and 'sentence' in node.props and
                    node.props['sentence'].operator == self.operators[0] and
                    node.props['sentence'].operand.operator == self.operators[1])
                    
    class OperatorDesignationRule(NodeRule):
        
        conditions = None
        
        def applies_to_node(self, node, branch):
            return (self.conditions != None and 'sentence' in node.props and
                    'designated' in node.props and node.props['sentence'].operator == self.conditions[0] and
                    node.props['designated'] == self.conditions[1])
                    
    class DoubleOperatorDesignationRule(NodeRule):
        
        conditions = None
        
        def applies_to_node(self, node, branch):
            return (self.conditions != None and 'sentence' in node.props and
                    node.props['sentence'].operator == self.conditions[0][0] and
                    node.props['sentence'].operand.operator == self.conditions[0][1] and
                    node.props['designated'] == self.conditions[1])

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
        
    num_constant_chars = 4
    @staticmethod
    def get_new_constant(branch):
        constants = list(TableauxSystem.get_constants_on_branch(branch))
        if not len(constants):
            return constant(0, 0)
        index = 0
        subscript = 0
        c = constant(index, subscript)
        while c in constants:
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
    
    def read_item(self, chars):
        self.assert_current_in(chars)
        index = chars.index(self.current())
        self.advance()
        subscript = self.read_subscript()
        return [index, subscript]
        
    def read_subscript(self):
        sub = ['0']
        while (self.current() and self.current().isdigit()):
            sub.append(self.current())
            self.advance()
        return int(''.join(sub))
        
    def read_atomic(self):
        return atomic(*self.read_item(self.achars))

    def read_variable(self):
        return variable(*self.read_item(self.vchars))

    def read_constant(self):
        return constant(*self.read_item(self.cchars))

    def read_predicate(self):    
        self.assert_current_in(self.upchars + self.pindex.keys())
        pchar = self.current()
        cpos = self.pos
        try:
            if pchar in self.upchars:
                index, subscript = self.read_item(self.upchars)
                return Vocabulary.get_predicate(index=index, subscript=subscript)
            else:
                index, subscript = self.read_item(self.pindex.keys())
                return Vocabulary.get_predicate(name=self.pindex[pchar][subscript])
        except Vocabulary.NoSuchPredicateError:
            raise Parser.ParseError('Undefined predicate symbol "' + pchar + '" at position ' + str(cpos))

    def read_parameters(self, num):
        parameters = []
        while len(parameters) < num:
            self.assert_current_in(self.cchars + self.vchars)
            cpos = self.pos
            if self.current() in self.cchars:
                parameters.append(self.read_constant())
            else:
                v = self.read_variable()
                if v not in list(self.bound_vars):
                    sub = str(v.subscript) if v.subscript > 0 else ''
                    raise Parser.ParseError("Unbound variable " + self.vchars[v.index] + sub + ' at position ' + str(cpos))
                parameters.append(v)
        return parameters

    def read_predicate_sentence(self):
        predicate = self.read_predicate()
        return predicate_sentence(predicate, self.read_parameters(predicate.arity))
        
    def read(self):
        return self.read_atomic()
        
    def user_predicate_indexes(self):
        indexes = []
        for index, symbol in self.pchars:
            if symbol not in self.pindex:
                indexes.append(index)
        return indexes
        