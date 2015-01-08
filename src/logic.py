"""
Copyright (C) 2014, Doug Owings. All Rights Reserved.
"""

import importlib, notations
from types import ModuleType

operators_list = [
    'Negation', 
    'Conjunction', 
    'Disjunction', 
    'Material Conditional', 
    'Material Biconditional',
    'Conditional', 
    'Biconditional', 
    'Possibility', 
    'Necessity'
]

operators = {
    'Negation'               : 1,
    'Conjunction'            : 2,
    'Disjunction'            : 2,
    'Material Conditional'   : 2,
    'Material Biconditional' : 2,
    'Conditional'            : 2,
    'Biconditional'          : 2,
    'Possibility'            : 1,
    'Necessity'              : 1
}

quantifiers = [
    'Universal',
    'Existential'
]

modal_operators = {
    'Possibility',
    'Necessity'
}

conditional_operators = {
    'Conditional',
    'Material Conditional'
}

biconditional_operators = {
    'Biconditional',
    'Material Biconditional'
}

system_predicates_list  = ['Identity', 'Existence']
system_predicates_index = {
    -1: { 0: 'Identity'},
    -2: { 0: 'Existence'}
}

# The number of symbols is fixed to allow multiple notations.
num_var_symbols            = 4
num_const_symbols          = 4
num_atomic_symbols         = 5
num_user_predicate_symbols = 4

def parse(string, vocabulary=None, notation='polish'):
    """
    Parse a string and return a sentence. If *vocabulary* is passed, the parser will
    use its user-defined predicates. The *notation* parameter can be either a notation 
    module or a string of the module name. Example::
        
        sentence = parse('Kab')
        
    """
    if vocabulary is None:
        vocabulary = Vocabulary()
    if isinstance(notation, str):
        notation = importlib.import_module('notations.' + notation)
    assert isinstance(notation, ModuleType), "notation parameter must be a module or string"
    return notation.Parser(vocabulary).parse(string)

class argument(object):
    """
    Create an argument::

        premises = [parse('Aab'), parse('Nb')]
        conclusion = parse('a')
        arg = argument(conslusion, premises)

    """

    def __init__(self, conclusion=None, premises=[]):
        self.premises = premises
        self.conclusion = conclusion

    def __repr__(self):
        return [self.premises, self.conclusion].__repr__()

def tableau(logic, arg):
    """
    Create a tableau for the given logic and argument. Example::

        from logics import cpl
        proof = tableau(cpl, arg)
        proof.build()
        if proof.valid:
            print "Valid"
        else:
            print "Invalid"

    """
    return TableauxSystem.Tableau(logic, arg)

def atomic(index, subscript):
    """
    Return an atomic sentence represented by the given index and subscript integers. Example::

        sentence = atomic(0, 0)
        assert sentence == parse('a')

        sentence = atomic(2, 3)
        assert sentence == parse('c3')

    """
    return Vocabulary.AtomicSentence(index, subscript)
        
def constant(index, subscript):
    """
    Return a constant representend by the given index and subscript integers::

        param = constant(0, 0)

    """
    return Vocabulary.Constant(index, subscript)

def variable(index, subscript):
    """
    Return a variable representend by the given index and subscript integers::

        param = variable(0, 0)

    """
    return Vocabulary.Variable(index, subscript)

def predicate_sentence(predicate, parameters, vocabulary=None):
    """
    Return a predicate sentence for the given predicate and parameters. *predicate* can 
    either be the name of a predicate or a predicate object. Example using system predicates::

        param = constant(0, 0)
        sentence = predicate_sentence('Existence', [param])

    Using user-defined predicates::
    
        vocab = Vocabulary([('is tall', 0, 0, 1)])
        param = constant(0, 0)
        sentence = predicate_sentence('is tall', [param], vocab)
        
    """
    return Vocabulary.PredicateSentence(predicate, parameters, vocabulary)
                     
def operate(operator, operands):
    """
    Apply an operator to a list of sentences (operands). Example::
    
        lhs = parse('a')
        rhs = parse('b')
        sentence = operate('Material Biconditional', [lhs, rhs])
        
    """
    return Vocabulary.MolecularSentence(operator, operands)

def negate(sentence):
    """
    Negate a sentence and return the negated sentence. This is shorthand for 
    *operate('Negation', [sentence])*.
    """
    return Vocabulary.MolecularSentence('Negation', [sentence])

def quantify(quantifier, variable, sentence):
    """
    Return a quanitified sentence for the given quantifier, bound variable and
    inner sentence::

        v = variable(0, 0)
        sentence = quantify('Universal', v, predicate_sentence('Existence', [v]))
        
    """
    return Vocabulary.QuantifiedSentence(quantifier, variable, sentence)
        
def arity(operator):
    """
    Get the arity of an operator. Example::

        assert arity('Conjunction') == 2

    """
    return operators[operator]

def is_constant(obj):
    """
    Check whether a parameter is a constant. Example::

        assert is_constant(constant(0, 0))
        assert not is_constant(variable(0, 0))
        assert not is_constant([0, 0]) # must be an instance of Vocabulary.Constant

    """
    return isinstance(obj, Vocabulary.Constant)

def is_variable(obj):
    """
    Check whether a parameter is a variable. Example::

        assert is_constant(variable(0, 0))
        assert not is_constant(constant(0, 0))
        assert not is_constant([0, 0]) # must be an instance of Vocabulary.Variable

    """
    return isinstance(obj, Vocabulary.Variable)

class Vocabulary(object):
    """
    Create a new vocabulary. *predicate_defs* is a list of tuples (name, index, subscript, arity)
    defining user predicates. Example::
        
        vocab = Vocabulary([
            ('is tall', 0, 0, 1),
            ('is taller than', 0, 1, 2),
            ('between', 1, 0, 3)
        ])
        
    """
    
    class Predicate(object):
        
        def __init__(self, name, index, subscript, arity):
            self.name      = name
            self.index     = index
            self.arity     = arity
            self.subscript = subscript

    class PredicateError(Exception):
        pass
        
    class NoSuchPredicateError(PredicateError):
        pass
            
    class PredicateArityMismatchError(PredicateError):
        pass
        
    class PredicateIndexMismatchError(PredicateError):
        pass
        
    def __init__(self, predicate_defs=None):
        self.user_predicates       = {}
        self.user_predicates_list  = []
        self.user_predicates_index = {}
        if predicate_defs:
            for info in predicate_defs:
                assert len(info) == 4, "Prediate declarations must be 4-tuples (name, index, subscript, arity)"
                self.declare_predicate(*info)
        
    def get_predicate(self, name=None, index=None, subscript=None):
        """
        Get a defined predicate, either by name, or by index and subscript. This includes system
        predicates::
        
            vocab = Vocabulary()
            predicate = vocab.get_predicate('Identity')
            
        Or user-defined predicates::
        
            vocab = Vocabulary([('is tall', 0, 0, 1)])
            assert vocab.get_predicate('is tall') == vocab.get_predicate(index=0, subscript=0)
            
        """
        if name != None:
            if name in self.system_predicates:
                return self.system_predicates[name]
            if name in self.user_predicates:
                return self.user_predicates[name]
            raise Vocabulary.NoSuchPredicateError(name)
        if index != None and subscript != None:
            idx = str([index, subscript])
            if index < 0:
                if subscript not in system_predicates_index[index]:
                    raise Vocabulary.NoSuchPredicateError(idx)
                return system_predicates[system_predicates_index[index][subscript]]
            if idx not in self.user_predicates_index:
                raise Vocabulary.NoSuchPredicateError(idx)
            return self.user_predicates_index[idx]
        raise Exception('Not enough information to get predicate')

    def declare_predicate(self, name, index, subscript, arity):
        """
        Declare a user-defined predicate::
        
            vocab = Vocabulary()
            vocab.declare_predicate(name='is tall', index=0, subscript=0, arity=1)
            
        """
        if name in system_predicates:
            raise Vocabulary.PredicateError('Cannot declare system predicate: ' + name)
        if name in self.user_predicates:
            raise Vocabulary.PredicateError('Predicate already declared: ' + name)
        predicate = Vocabulary.Predicate(name, index, subscript, arity)
        self.user_predicates[name] = predicate
        self.user_predicates_list.append(name)
        if index >= 0:
            self.user_predicates_index[str([index, subscript])] = predicate    
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
        
        operator   = None
        quantifier = None
        predicate  = None
        
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
            self.index     = index
            self.subscript = subscript

        def substitute(self, constant, variable):
            return self
            
        def constants(self):
            return set()
            
        def variables(self):
            return set()
            
    class PredicateSentence(Sentence):
        
        def __init__(self, predicate, parameters, vocabulary=None):
            if isinstance(predicate, str):
                if predicate in system_predicates:
                    predicate = system_predicates[predicate]
                elif vocabulary is None:
                    raise Vocabulary.PredicateError(predicate + " is not a system predicate, and no vocabulary was passed.")
                else:
                    predicate = vocabulary.get_predicate(predicate)    
            if len(parameters) != predicate.arity:
                raise Vocabulary.PredicateArityMismatchError('Expecting ' + predicate.arity + ' parameters for predicate ' + 
                str([index, subscript]) + ', got ' + arity + ' instead.')
            self.predicate  = predicate
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
            self.variable   = variable
            self.sentence   = sentence
            
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

system_predicates = {
    'Identity'  : Vocabulary.Predicate('Identity', -1, 0, 2),
    'Existence' : Vocabulary.Predicate('Existence', -2, 0, 1)
}
            
class TableauxSystem(object):
    
    class Tableau(object):
        """
        Represents a tableau proof of an argument for the given logic.
        """
        
        #: Whether the proof is valid, set after the proof is finished.
        valid = None

        #: The branches on the tree.
        branches = set()

        #: A history of rule applications.
        history = []

        #: A tree-map structure of the tableau, generated after the proof is finished.
        tree = dict()

        #: Whether the proof is finished.
        finished = False
        
        def __init__(self, logic, argument):
            self.logic = logic
            self.argument = argument
            self.rules = [Rule(self) for Rule in logic.TableauxRules.rules]
            self.branches = set()
            self.history = []
            self.finished = False
            self.build_trunk()
            
        def build(self):
            """
            Build the tableau and return *self*.
            """
            while not self.finished:
                self.step()
            return self

        def step(self):
            """
            Perform the next rule application, if any.
            """
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
                
        def open_branches(self):
            """
            Return the set of open branches on the tableau.
            """
            return {branch for branch in self.branches if not branch.closed}
                              
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

        def branch_multi(self, other_branch=None, num=1):
            return [self.branch(other_branch) for x in range(num)]
            
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
                    
        def finish(self):
            self.finished = True
            self.tree = self.structure(self.branches)
            self.valid = (self.finished and len(self.open_branches()) == 0)
            
        def __repr__(self):
            return {
                'argument'      : self.argument,
                'branches'      : len(self.branches),
                'rules_applied' : len(self.history),
                'finished'      : self.finished
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
            raise Exception(NotImplemented)
            
        def apply(self, target):
            raise Exception(NotImplemented)
        
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
            raise Exception(NotImplemented)
            
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

    class OperatorQuantifierRule(NodeRule):

        connectives = None

        def applies_to_node(self, node, branch):
            return (self.connectives != None and 'sentence' in node.props and
                    node.props['sentence'].operator == self.connectives[0] and
                    node.props['sentence'].operand.quantifier == self.connectives[1])

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

    class QuantifierDesignationRule(NodeRule):

        conditions = None

        def applies_to_node(self, node, branch):
            return (self.conditions != None and 'sentence' in node.props and
                    'designated' in node.props and node.props['sentence'].quantifier == self.conditions[0] and
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
            if 'worlds' in node.props:
                worlds.update(node.props['worlds'])
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
            
    achars  = []
    ochars  = {}
    cchars  = []
    vchars  = []
    qchars  = {}
    upchars = []
    spchars = ['I', 'J']
    wschars = set([' '])
    
    def __init__(self, vocabulary):
        self.vocabulary = vocabulary
        
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
        self.assert_current_in(self.upchars + self.spchars)
        pchar = self.current()
        cpos = self.pos
        try:
            if pchar in self.upchars:
                index, subscript = self.read_item(self.upchars)
            else:
                index, subscript = self.read_item(self.spchars)
                index = (index + 1) * -1
                if index not in system_predicates_index or subscript not in system_predicates_index[index]:
                    raise Vocabulary.NoSuchPredicateError()
            return self.vocabulary.get_predicate(index=index, subscript=subscript)
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
        
    @staticmethod
    def spchar(index):
        index = index * -1 - 1
        return Parser.spchars[index]