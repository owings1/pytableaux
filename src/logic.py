# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ------------------
#
# pytableaux - logic base module

import importlib, notations, os
from types import ModuleType

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, '..'))
with open(os.path.join(base_dir, 'VERSION'), 'r') as f:
    version = f.read().strip()

copyright = '2014-2017, Doug Owings. Released under the GNU Affero General Public License v3 or later'
source_href = 'https://bitbucket.org/owings1/pytableaux'

# name : arity
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

# default display ordering
operators_list = [
    'Negation'               ,
    'Conjunction'            ,
    'Disjunction'            ,
    'Material Conditional'   ,
    'Material Biconditional' ,
    'Conditional'            ,
    'Biconditional'          ,
    'Possibility'            ,
    'Necessity'
]

quantifiers_list = [
    'Universal',
    'Existential'
]

system_predicates_list  = [
    'Identity',
    'Existence'
]

system_predicates_index = {
    # negative indexes for system predicates, value is subscript : name.
    -1 : { 0 : 'Identity'  },
    -2 : { 0 : 'Existence' }
}

# The number of symbols is fixed to allow multiple notations.
num_var_symbols       = 4
num_const_symbols     = 4
num_atomic_symbols    = 5
num_predicate_symbols = 4

# Test vocabulary predicate data for example_validities, etc.
test_pred_data = [
    ['is F', 0, 0, 1],
    ['is G', 1, 0, 1],
    ['is H', 2, 0, 1],
    ['Os'  , 3, 0, 2],
    ['O1s' , 3, 1, 2]
]

def atomic(index, subscript):
    """Return an atomic sentence represented by the given index and subscript integers.
    Examples::

        a  = atomic(index=0, subscript=0)
        a0 = atomic(0, 0)
        assert a == a0
        
        b  = atomic(1, 0)
        a4 = atomic(0, 4)
        
        c3 = atomic(2, 3)
        assert sentence2 == parse('c3', notation='polish') # c has index 2 in polish notation

    """
    return Vocabulary.AtomicSentence(index, subscript)

def negate(sentence):
    """Negate a sentence and return the negated sentence. This is shorthand for 
    *operate('Negation', [sentence])*. Example::

        a = atomic(0, 0)
        # not a
        sentence = negate(a)

    """
    return Vocabulary.MolecularSentence('Negation', [sentence])

def operate(operator, operands):
    """Apply an operator to a list of sentences (operands).
    Examples::

        a = atomic(0, 0)
        b = atomic(1, 0)

        # a or b
        sentence2 = operate('Disjunction', [a, b])

        # a or b, and not b
        sentence4 = operate('Conjunction', [sentence2, negate(b)])

        # if a or b, and not b, then a
        sentence5 = operate('Conditional', [sentence4, a])

    Available operators are:

    +------------------------+-------+
    | Operator Name          | Arity |
    +========================+=======+
    | Negation               | 1     |
    +------------------------+-------+
    | Conjunction            | 2     |
    +------------------------+-------+
    | Disjunction            | 2     |
    +------------------------+-------+
    | Material Conditional   | 2     |
    +------------------------+-------+
    | Material Biconditional | 2     |
    +------------------------+-------+
    | Conditional            | 2     |
    +------------------------+-------+
    | Biconditional          | 2     |
    +------------------------+-------+
    | Possibility            | 1     |
    +------------------------+-------+
    | Necessity              | 1     |
    +------------------------+-------+

    """
    return Vocabulary.MolecularSentence(operator, operands)

def constant(index, subscript):
    """Return a constant representend by the given index and subscript integers.
    Example::

        m = constant(0, 0)

    """
    return Vocabulary.Constant(index, subscript)

def variable(index, subscript):
    """
    Return a variable representend by the given index and subscript integers::

        x = variable(0, 0)

    """
    return Vocabulary.Variable(index, subscript)

def predicate_sentence(predicate, parameters, vocabulary=None):
    """
    Return a predicate sentence for the given predicate and parameters. *predicate* can 
    either be the name of a predicate or a predicate object. Examples using system predicates
    (Existence, Identity)::

        m = constant(0, 0)
        sentence = predicate_sentence('Existence', [m])

        n = constant(1, 0)
        sentence2 = predicate_sentence('Identity', [m, n])

    Examples using a vocabulary of user-defined predicates::

        vocab = Vocabulary([('is tall', 0, 0, 1)])
        m = constant(0, 0)
        # m is tall
        sentence = predicate_sentence('is tall', [m], vocab)

        vocab.declare_predicate(name='is between', index=1, subscript=0, arity=3)
        n = constant(1, 0)
        o = constant(2, 0)
        # m is between n and o
        sentence2 = predicate_sentence('is between', [m, n, o], vocab)

    """
    return Vocabulary.PredicateSentence(predicate, parameters, vocabulary)

def quantify(quantifier, variable, sentence):
    """
    Return a quanitified sentence for the given quantifier, bound variable and
    inner sentence. Example using the Identity system predicate::

        x = variable(0, 0)
        # x is identical to x
        open_sentence = predicate_sentence('Identity', [x, x])
        # for all x, x is identical to x
        sentence = quantify('Universal', x, open_sentence)

    Examples using a vocabulary of user-defined predicates::

        vocab = Vocabulary([
            ('is a bachelor', 0, 0, 1),
            ('is unmarried' , 1, 0, 1)
        ])
        x = variable(0, 0)
        # x is a bachelor
        open_sentence = predicate_sentence('is a bachelor', [x], vocab)
        # there exists an x, such that x is a bachelor
        sentence = quantify('Existential', x, open_sentence)

        # x is unmarried
        open_sentence2 = predicate_sentence('is unmarried', [x], vocab)
        # if x is a bachelor, then x is unmarried
        open_sentence3 = operate('Conditional', [open_sentence, open_sentence2])
        # for all x, if x is a bachelor then x is unmarried
        sentence2 = quantify('Universal', x, open_sentence3)

    """
    return Vocabulary.QuantifiedSentence(quantifier, variable, sentence)

def parse(string, vocabulary=None, notation='polish'):
    """
    Parse a string and return a sentence. If *vocabulary* is passed, the parser will
    use its user-defined predicates. The *notation* parameter can be either a notation 
    module or a string of the module name. Currently the only implemented notation is
    polish. Example::

        sentence = parse('Kab', notation='polish')
        assert sentence == operate('Conjunction', [atomic(0, 0), atomic(1, 0)])

    Example using user-defined predicates from a vocabulary::
    
        vocab = Vocabulary([('is tall', 0, 0, 1)])
        # m is tall
        sentence = parse('Fm', vocab, 'polish')
        assert sentence == predicate_sentence(vocab.get_predicate('is tall'), [constant(0, 0)])

    """
    if vocabulary is None:
        vocabulary = Vocabulary()
    notation = _get_module('notations', notation)
    return notation.Parser(vocabulary).parse(string)

class argument(object):
    """
    Create an argument::

        a = atomic(0, 0)
        b = atomic(1, 0)
        # if a then b
        premise2 = operate('Conditional', [a, b])
        # from a, and if a then b, it follows that b
        arg = argument(conclusion=b, premises=[a, premise2])

    """

    def __init__(self, conclusion=None, premises=[]):
        self.premises   = premises
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

def arity(operator):
    """
    Get the arity of an operator. Examples::

        assert arity('Conjunction') == 2
        assert arity('Negation') == 1
        assert arity(operate('Negation', [atomic(0, 0)]).operator) == 1

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

def get_logic(arg):
    """
    Get the logic module from the specified name. Example::

        assert get_logic('fde') == logics.fde
        assert get_logic('logics.fde') == logics.fde
        assert get_logic('FDE') == logics.fde
        assert get_logic(logics.fde) == logics.fde
    """
    return _get_module('logics', arg)

def _get_module(package, arg):    
    if isinstance(arg, ModuleType):
        return arg
    if isinstance(arg, str):
        if '.' not in arg:
            arg = package + '.' + arg
        return importlib.import_module(arg.lower())
    raise Exception("Argument must be module or string")


def get_test_vocabulary():
    return Vocabulary(test_pred_data)

class Vocabulary(object):
    """
    Create a new vocabulary. *predicate_defs* is a list of tuples (name, index, subscript, arity)
    defining user predicates. Example::

        vocab = Vocabulary([
            ('is tall',        0, 0, 1),
            ('is taller than', 0, 1, 2),
            ('between',        1, 0, 3)
        ])

    """

    class Predicate(object):

        def __init__(self, name, index, subscript, arity):
            self.name      = name
            self.arity     = arity
            self.index     = index
            self.subscript = subscript

    class PredicateError(Exception):
        pass

    class PredicateAlreadyDeclaredError(PredicateError):
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
            if name in system_predicates:
                return system_predicates[name]
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
        raise Vocabulary.PredicateError('Not enough information to get predicate')

    def declare_predicate(self, name, index, subscript, arity):
        """
        Declare a user-defined predicate::

            vocab = Vocabulary()
            predicate = vocab.declare_predicate(name='is tall', index=0, subscript=0, arity=1)
            assert predicate == vocab.get_predicate('is tall')
            assert predicate == vocab.get_predicate(index=0, subscript=0)
            
            # predicates cannot be re-declared
            try:
                vocab.declare_predicate('is tall', index=1, subscript=2, arity=3)
            except Vocabulary.PredicateAlreadyDeclaredError:
                assert true
            else:
                assert false

        """
        if name in system_predicates:
            raise Vocabulary.PredicateAlreadyDeclaredError('Cannot declare system predicate: ' + name)
        if name in self.user_predicates:
            raise Vocabulary.PredicateAlreadyDeclaredError('Predicate already declared: ' + name)
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
            return other != None and self.__dict__ == other.__dict__

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

        def next(self):
            if self.index < num_atomic_symbols - 1:
                index = self.index + 1
                subscript = self.subscript
            else:
                index = 0
                subscript = self.subscript + 1
            return Vocabulary.AtomicSentence(index, subscript)

    class PredicateSentence(Sentence):

        def __init__(self, predicate, parameters, vocabulary=None):
            if isinstance(predicate, str):
                if predicate in system_predicates:
                    predicate = system_predicates[predicate]
                elif vocabulary is None:
                    raise Vocabulary.NoSuchPredicateError(predicate + " is not a system predicate, and no vocabulary was passed.")
                else:
                    predicate = vocabulary.get_predicate(predicate)    
            if len(parameters) != predicate.arity:
                raise Vocabulary.PredicateArityMismatchError('Expecting ' + predicate.arity + ' parameters for predicate ' + 
                str([index, subscript]) + ', got ' + arity + ' instead.')
            self.predicate  = predicate
            self.parameters = parameters
            self.vocabulary = vocabulary

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
            if self.sentence.is_quantified():
                return Vocabulary.QuantifiedSentence(self.sentence.quantifier, self.sentence.variable, self.sentence.substitute(constant, variable))
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

    @staticmethod
    def get_example_quantifier_sentence(quantifier):
        vocab = Vocabulary([('is F', 0, 0, 1), ('is G', 1, 0, 1)])
        x = variable(0, 0)
        x_is_f = predicate_sentence('is F', [x], vocab)
        if quantifier == 'Universal':
            x_is_g = predicate_sentence('is G', [x], vocab)
            s = operate('Material Conditional', [x_is_f, x_is_g])
            return quantify(quantifier, x, s)
        return quantify(quantifier, x, x_is_f)

system_predicates = {
    'Identity'  : Vocabulary.Predicate('Identity',  -1, 0, 2),
    'Existence' : Vocabulary.Predicate('Existence', -2, 0, 1)
}

class TableauxSystem(object):

    class Tableau(object):
        """
        Represents a tableau proof of an argument for the given logic.
        """

        def __init__(self, logic, argument):
            #: A tableau is finished when no more rules can apply.
            self.finished = False
            
            #: An argument is proved (valid) when its finished tableau has no open branches.
            self.valid = None
            
            #: The set of branches on the tableau.
            self.branches = set()
            
            #: A tree-map structure of the tableau, generated after the proof is finished.
            self.tree = dict()
            
            # A history of rule applications.
            self.history = []

            #: A reference to the logic, if given
            self.logic = None

            #: The rule instances of the logic, if given
            self.rules = []

            #: The argument of the tableau, if given
            self.argument = argument

            if logic != None:
                self.logic = get_logic(logic)
                self.rules = [Rule(self) for Rule in self.logic.TableauxRules.rules]
            
            if argument != None:
                self.build_trunk()

        def build(self):
            """
            Build the tableau. Returns self.
            """
            while not self.finished:
                self.step()
            return self

        def step(self):
            if self.finished:
                return False
            for rule in self.rules:
                target = rule.applies()
                if target:
                    rule.apply(target)
                    application = { 'rule' : rule, 'target' : target }
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
            structure = { 'nodes' : [], 'children' : [], 'closed' : False }
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

        def branch(self, other_branch=None):
            """
            Return a new branch on the tableau containing the nodes of the given branch, if any.
            """
            if not other_branch:
                branch = TableauxSystem.Branch()
            else:
                branch = other_branch.copy()
                self.branches.discard(other_branch) # ?? can't remember why I do this...
            self.branches.add(branch)
            return branch

        def branch_multi(self, other_branch=None, num=1):
            """
            Return a list of new branches from the given branch.
            """
            return [self.branch(other_branch) for x in range(num)]

        def build_trunk(self):
            return self.logic.TableauxSystem.build_trunk(self, self.argument)

        def finish(self):
            """
            Mark the tableau as finished. Computes the 'valid' property and builds the structure
            into the 'tree' property. Returns self.
            """
            self.finished = True
            self.valid    = len(self.open_branches()) == 0
            self.tree     = self.structure(self.branches)
            return self

        def __repr__(self):
            return {
                'argument'      : self.argument,
                'branches'      : len(self.branches),
                'rules_applied' : len(self.history),
                'finished'      : self.finished
            }.__repr__()

    class Branch(object):
        """
        Represents a tableau branch.
        """

        def __init__(self):
            #: A branch is closed by a closure balls rule.
            self.closed = False
            self.ticked_nodes = set()
            self.nodes = []

        def has(self, props, ticked=None):
            for node in self.get_nodes(ticked=ticked):
                if node.has_props(props):
                    return True
            return False

        def add(self, node):
            """
            Add a node (Node object or dict of props). Returns self.
            """
            if not isinstance(node, TableauxSystem.Node):
                node = TableauxSystem.Node(props=node)
            self.nodes.append(node)
            return self

        def update(self, nodes):
            """
            Add multiple nodes. Returns self.
            """
            for node in nodes:
                self.add(node)
            return self

        def tick(self, node):
            """
            Tick a node for the branch. Returns self.
            """
            self.ticked_nodes.add(node)
            node.ticked = True
            return self

        def close(self):
            """
            Close the branch. Returns self.
            """
            self.closed = True
            return self

        def get_nodes(self, ticked=None):
            """
            Return the nodes, optionally filtered by ticked status.
            """
            if ticked == None:
                return self.nodes
            return [node for node in self.nodes if ticked == (node in self.ticked_nodes)]

        def copy(self):
            branch = TableauxSystem.Branch()
            branch.nodes = list(self.nodes)
            branch.ticked_nodes = set(self.ticked_nodes)
            return branch

        def worlds(self):
            """
            Return the set of worlds that appear on the branch.
            """
            worlds = set()
            for node in self.nodes:
                worlds.update(node.worlds())
            return worlds

        def new_world(self):
            """
            Return a new world that does not appear on the branch.
            """
            worlds = self.worlds()
            if not len(worlds):
                return 0
            return max(worlds) + 1

        def constants(self):
            """
            Return the set of constants that appear on the branch.
            """
            constants = set()
            for node in self.nodes:
                if 'sentence' in node.props:
                    constants.update(node.props['sentence'].constants())
            return constants

        def new_constant(self):
            """
            Return a new constant that does not appear on the branch.
            """
            constants = list(self.constants())
            if not len(constants):
                return constant(0, 0)
            index = 0
            subscript = 0
            c = constant(index, subscript)
            while c in constants:
                index += 1
                if index == num_const_symbols:
                    index = 0
                    subscript += 1
                c = constant(index, subscript)
            return c

        def __repr__(self):
            return self.nodes.__repr__()

    class Node(object):
        """
        Represents a node on a branch.
        """

        def __init__(self, props={}):
            #: A dictionary of properties for the node.
            self.props = props
            self.ticked = False

        def has_props(self, props):
            for prop in props:
                if prop not in self.props or not props[prop] == self.props[prop]:
                    return False
            return True

        def worlds(self):    
            worlds = set()
            if 'world' in self.props:
                worlds.add(self.props['world'])
            if 'world1' in self.props:
                worlds.add(self.props['world1'])
            if 'world2' in self.props:
                worlds.add(self.props['world2'])
            if 'worlds' in self.props:
                worlds.update(self.props['worlds'])
            return worlds
            
        def __repr__(self):
            return self.__dict__.__repr__()

    class Rule(object):
        """
        Base interface class for a tableau rule. Rule classes are instantiated per tableau instance.
        """

        def __init__(self, tableau):
            """
            Instantiate the rule for the tableau.
            """
            #: Reference to the tableau for which the rule is instantiated.
            self.tableau = tableau

        def applies(self):
            """
            Whether the rule applies to the tableau. Implementations should return true/false or a target object.
            """
            raise Exception(NotImplemented)

        def apply(self, target):
            """
            Apply the rule to the tableau. Assumes that applies() has returned true. Implementations should
            modify the tableau directly, with no return value.
            """
            raise Exception(NotImplemented)

        def example(self):
            """
            Add example branches/nodes sufficient for applies() to return true. Implementations should modify
            the tableau directly, with no return value. Used for building examples/documentation.
            """
            raise Exception(NotImplemented)

        def __repr__(self):
            return self.__class__.__name__

    class BranchRule(Rule):
        """
        A branch rule applies to an open branch on a tableau. This base class implements the applies() method
        by finding the first open branch on the tableau to which the abstract method applies_to_branch() returns
        a non-false value.
        """

        def applies(self):
            for branch in self.tableau.open_branches():
                target = self.applies_to_branch(branch)
                if target:
                    return target
            return False

        def applies_to_branch(self, branch):
            """
            Abstract method that must be implemented in sub-classes. Should return a target object.
            """
            raise Exception(NotImplemented)

    class ClosureRule(BranchRule):
        """
        A closure rule has a fixed apply() method that marks the branch as closed. Sub-classes should
        implement the applies_to_branch() method.
        """

        def applies_to_branch(self, branch):
            raise Exception(NotImplemented)

        def apply(self, branch):
            branch.close()

    class NodeRule(BranchRule):
        """
        A node rule has a fixed applies() method that searches open branches and queries the applies_to_node()
        method. If it applies, return a target dict with props 'node' and 'branch'.
        """

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

        def example(self):
            self.tableau.branch().add(self.example_node())

        def example_node(self):
            raise Exception(NotImplemented)

    class ConditionalNodeRule(NodeRule):

        ticked      = False
        modal       = None
        negated     = None
        operator    = None
        quantifier  = None
        designation = None

        def applies_to_node(self, node, branch):
            if self.ticked != None and self.ticked != (node in branch.ticked_nodes):
                return False
            if self.modal != None:
                modal = len(node.worlds()) > 0
                if self.modal != modal:
                    return False
            sentence = operator = quantifier = None
            if 'sentence' in node.props:
                sentence = node.props['sentence']
                operator = sentence.operator
                quantifier = sentence.quantifier
            if self.negated != None:
                negated = operator == 'Negation'
                if not sentence or negated != self.negated:
                    return False
                if negated:
                    sentence = sentence.operand
                    operator = sentence.operator
                    quantifier = sentence.quantifier
            if self.operator != None:
                if self.operator != operator:
                    return False
            elif self.quantifier != None:
                if self.quantifier != quantifier:
                    return False
            if self.designation != None:
                if 'designated' not in node.props or node.props['designated'] != self.designation:
                    return False
            return True

        def example_node(self):
            props = {}
            if self.modal:
                props['world'] = 0
            if self.designation != None:
                props['designated'] = self.designation
            sentence = None
            a = atomic(0, 0)
            if self.operator != None:
                params = []
                n = arity(self.operator)
                if n > 0:
                    params.append(a)
                for i in range(n - 1):
                    params.append(params[-1].next())
                sentence = operate(self.operator, params)
            elif self.quantifier != None:
                sentence = Vocabulary.get_example_quantifier_sentence(self.quantifier)
            if self.negated:
                if sentence == None:
                    sentence = a
                sentence = negate(sentence)
            if sentence != None:
                props['sentence'] = sentence
            return props

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
        sub = []
        while (self.current() and self.current().isdigit()):
            sub.append(self.current())
            self.advance()
        if not len(sub):
            sub.append('0')
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