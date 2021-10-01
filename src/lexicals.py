from fixed import num_atomic_symbols, num_const_symbols, num_predicate_symbols, \
    num_var_symbols, operators, system_predicates_index, system_predicates_list

from errors import PredicateError, IndexTooLargeError, PredicateArityError, \
    PredicateSubscriptError, PredicateAlreadyDeclaredError, NoSuchPredicateError, \
    PredicateArityMismatchError, PredicateIndexMismatchError, OperatorError, \
    NoSuchOperatorError, OperatorArityMismatchError

from past.builtins import basestring

class LexicalItem(object):
    # Base LexicalItem class for comparison, hashing, and sorting.

    def sort_tuple(self):
        # Sort tuple should always consist of numbers, or tuples with numbers.
        # This is also used in hashing, so equal objects should have equal hashes.
        raise NotImplementedError()

    def ident(self):
        # Equality/inequality identifier. By default, this delegates to sort_tuple.
        return self.sort_tuple()

    # Sorting implementation. The Vocabulary class defines canonical ordering for
    # each type of lexical item, so we can sort lists with mixed classes, e.g.
    # constants and variables, different sentence types, etc. This class takes
    # care of ensuring different types are not considered equal (e.g. constant(0, 0),
    # variable(0, 0), atomic(0, 0)) and are still sorted properly.
    #
    # This is the reason for _lexrank, and __lexorder, on the Vocabulary class,
    # as well as similar properties on QuantifiedSentence (for quantifiers), and
    # OperatedSentence (for operators). Basically anything that cannot be
    # converted to a number by which we can meaningfully sort needs to be
    # considered specially, i.e. classes, operators, and quantifiers.
    def __lt__(self, other):
        a, b = self.__getcmp(other)
        return a < b

    def __le__(self, other):
        a, b = self.__getcmp(other)
        return a <= b

    def __gt__(self, other):
        a, b = self.__getcmp(other)
        return a > b

    def __ge__(self, other):
        a, b = self.__getcmp(other)
        return a >= b

    def __getcmp(self, other):
        r1, r2 = Vocabulary._lexrank(self, other)
        if r1 == r2:
            return (self.sort_tuple(), other.sort_tuple())
        return (r1, r2)

    # Default equals and hash implementation is based on sort_tuple.
    #
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    #
    # - If a class does not define __eq__ it should not define __hash__.
    #
    # - A class that overrides __eq__ and does not  __hash__ will have its
    #    __hash__ implicitly set to None.
    #

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.ident() == other.ident()
        )

    def __ne__(self, other):
        return (
            not isinstance(other, self.__class__) or
            self.ident() != other.ident()
        )

    def __hash__(self):
        return hash(self.sort_tuple())

class Parameter(LexicalItem):

    def __init__(self, index, subscript):
        self.index = index
        self.subscript = subscript

    def is_constant(self):
        return isinstance(self, Constant)

    def is_variable(self):
        return isinstance(self, Variable)

    def sort_tuple(self):
        # Sort constants and variables by index, subscript
        return (self.index, self.subscript)

    def __repr__(self):
        return (self.__class__.__name__, self.index, self.subscript).__repr__()

class Constant(Parameter):

    def __init__(self, index, subscript):
        if index >= num_const_symbols:
            raise IndexTooLargeError(
                "Index too large {0}".format(str(index))
            )
        super().__init__(index, subscript)

class Variable(Parameter):

    def __init__(self, index, subscript):
        if index >= num_var_symbols:
            raise IndexTooLargeError(
                "Index too large {0}".format(str(index))
            )
        super().__init__(index, subscript)

class Predicate(LexicalItem):

    def __init__(self, name, index, subscript, arity):
        if index >= num_predicate_symbols:
            raise IndexTooLargeError(
                "Predicate index too large {0}".format(str(index))
            )
        if arity == None or not isinstance(arity, int):
            raise PredicateArityError(
                'Predicate arity must be an integer'
            )
        if arity < 1:
            raise PredicateArityError(
                'Invalid predicate arity {0}'.format(str(arity))
            )
        if subscript == None or not isinstance(subscript, int):
            raise PredicateSubscriptError(
                'Predicate subscript must be an integer'
            )
        if subscript < 0:
            raise PredicateSubscriptError(
                'Invalid predicate subscript {0}'.format(str(subscript))
            )
        self.name      = name
        self.arity     = arity
        self.index     = index
        self.subscript = subscript

    def is_system_predicate(self):
        return self.index < 0

    def sort_tuple(self):
        # Sort predicates by index, subscript, arity
        return (self.index, self.subscript, self.arity)

    def __repr__(self):
        # Include the name for informational purposes, though it does not count
        # for its hash identity.
        name = self.name if self.name else '[Untitled]'
        return ((self.__class__.__name__, name) + self.sort_tuple()).__repr__()

class Sentence(LexicalItem):

    #: The operator, if any.
    operator = None

    #: The quantifier, if any.
    quantifier = None

    #: The predicate, if any.
    predicate = None

    #: The type (class name).
    type = None

    def __init__(self):
        self.type = self.__class__.__name__

    def is_atomic(self):
        """
        Whether this is an atomic sentence.
        """
        return isinstance(self, AtomicSentence)

    def is_predicated(self):
        """
        Whether this is a predicated sentence.
        """
        return isinstance(self, PredicatedSentence)

    def is_quantified(self):
        """
        Whether this a quantified sentence.
        """
        return isinstance(self, QuantifiedSentence)

    def is_operated(self):
        """
        Whether this is an operated sentence.
        """
        return isinstance(self, OperatedSentence)

    def is_literal(self):
        """
        Whether the sentence is a literal. Here a literal is either a
        predicated sentence, the negation of a predicated sentence,
        an atomic sentence, or the negation of an atomic sentence.
        """
        return self.is_atomic() or self.is_predicated() or (
            self.is_operated() and self.operator == 'Negation' and (
                self.operand.is_atomic() or
                self.operand.is_predicated()
            )
        )

    def substitute(self, new_param, old_param):
        """
        Recursively substitute ``new_param`` for all occurrences of ``old_param``.
        May return self, or a new sentence.
        """
        raise NotImplementedError()

    def constants(self):
        """
        Set of constants, recursive.
        """
        return set()

    def variables(self):
        """
        Set of variables, recursive.
        """
        return set()

    def atomics(self):
        """
        Set of atomic sentences, recursive.
        """
        return set()

    def predicates(self):
        """
        Set of predicates, recursive.
        """
        return set()

    def operators(self):
        """
        List of operators, recursive.
        """
        # TODO: Explain why operators and quantifiers are returned as a list,
        #       while everything else is returned as a set. I believe is has
        #       something to do tableau rule optimization, or maybe reading
        #       models. In any case, there might be a more consistent way.
        return list()

    def quantifiers(self):
        """
        List of quantifiers, recursive.
        """
        return list()

    def __repr__(self):
        # TODO: Consider removing this way of representing. I think it was
        #       useful in the early stages, but there are several reaons
        #       to abandon it: performance, consisitency, design, etc.
        # UPDATE:
        #   Error messages, e.g. in models, convert the sentence to a string,
        #   so removing this would make it harder to interpret errors. We could
        #   either find another way to represent them that is still helpful
        #   in errors, or generalize error handling and leave it to decide how
        #   to represent sentences.
        from notations import polish
        return polish.write(self)

class AtomicSentence(Sentence):

    def __init__(self, index, subscript):
        if index >= num_atomic_symbols:
            raise IndexTooLargeError(
                "Index too large {0}".format(str(index))
            )
        super().__init__()
        self.index     = index
        self.subscript = subscript

    def substitute(self, new_param, old_param):
        return self

    def atomics(self):
        return set([self])

    def next(self):
        if self.index < num_atomic_symbols - 1:
            index = self.index + 1
            subscript = self.subscript
        else:
            index = 0
            subscript = self.subscript + 1
        return AtomicSentence(index, subscript)

    def sort_tuple(self):
        # Sort atomic sentences by index, subscript
        return (self.index, self.subscript)

class PredicatedSentence(Sentence):

    def __init__(self, predicate, parameters, vocabulary=None):
        if isinstance(predicate, basestring):
            if predicate in system_predicates:
                predicate = system_predicates[predicate]
            elif vocabulary is None:
                raise NoSuchPredicateError(
                    "'{0}' is not a system predicate, and no vocabulary was passed.".format(predicate)
                )
            else:
                predicate = vocabulary.get_predicate(predicate)    
        if len(parameters) != predicate.arity:
            raise PredicateArityMismatchError(
                'Expecting {0} parameters for predicate {1}, got {2} instead.'.format(
                    predicate.arity, str([predicate.index, predicate.subscript]), len(parameters)
                )
            )
        super().__init__()
        self.predicate  = predicate
        self.parameters = parameters
        self.vocabulary = vocabulary

    def substitute(self, new_param, old_param):
        params = []
        for param in self.parameters:
            if param == old_param:
                params.append(new_param)
            else:
                params.append(param)
        return PredicatedSentence(self.predicate, params)

    def constants(self):
        return {param for param in self.parameters if param.is_constant()}

    def variables(self):
        return {param for param in self.parameters if param.is_variable()}

    def predicates(self):
        return set([self.predicate])

    def sort_tuple(self):
        # Sort predicated sentences by their predicate, then by their parameters
        return self.predicate.sort_tuple() + tuple(param.sort_tuple() for param in self.parameters)

class QuantifiedSentence(Sentence):

    def __init__(self, quantifier, variable, sentence):
        super().__init__()
        self.quantifier = quantifier
        self.variable   = variable
        self.sentence   = sentence

    def substitute(self, new_param, old_param):
        # Always return a new sentence.
        si = self.sentence
        r = si.substitute(new_param, old_param)
        return QuantifiedSentence(self.quantifier, self.variable, r)

    def constants(self):
        return self.sentence.constants()

    def variables(self):
        return self.sentence.variables()

    def atomics(self):
        return self.sentence.atomics()

    def predicates(self):
        return self.sentence.predicates()

    def operators(self):
        return self.sentence.operators()

    def quantifiers(self):
        return [self.quantifier] + self.sentence.quantifiers()

    def sort_tuple(self):
        # Sort quantified sentences first by their quanitfier, using fixed
        # lexical order (below), then by their variable, followed by their
        # inner sentence.
        return (self.__lexorder[self.quantifier], self.variable.sort_tuple(), self.sentence.sort_tuple())

    # Lexical sorting order.
    __lexorder = {'Existential': 0, 'Universal': 1}

class OperatedSentence(Sentence):

    def __init__(self, operator, operands):
        if operator not in operators:
            raise NoSuchOperatorError(
                "Unknown operator '{0}'.".format(operator)
            )
        arity = operators[operator]
        if len(operands) != arity:
            raise OperatorArityMismatchError(
                "Expecting {0} operands for operator '{1}', got {2}.".format(
                    arity, operator, len(operands)
                )
            )
        super().__init__()
        self.operator = operator
        self.operands = operands
        if len(operands) == 1:
            self.operand = operands[0]
            if operator == 'Negation':
                self.negatum = self.operand
        elif len(operands) > 1:
            self.lhs = operands[0]
            self.rhs = operands[-1]

    def substitute(self, new_param, old_param):
        # Always return a new sentence
        new_operands = [operand.substitute(new_param, old_param) for operand in self.operands]
        return OperatedSentence(self.operator, new_operands)

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

    def atomics(self):
        a = set()
        for operand in self.operands:
            a.update(operand.atomics())
        return a

    def predicates(self):
        p = set()
        for operand in self.operands:
            p.update(operand.predicates())
        return p

    def operators(self):
        ops = list()
        ops.append(self.operator)
        for operand in self.operands:
            ops.extend(operand.operators())
        return ops

    def quantifiers(self):
        qts = list()
        for operand in self.operands:
            qts.extend(operand.quantifiers())
        return qts

    def sort_tuple(self):
        # Sort operated sentences first by their operator, using fixed
        # lexical order (below), then by their operands.
        return (self.__lexorder[self.operator],) + tuple(s.sort_tuple() for s in self.operands)

    # Lexical sorting order. Perhaps there is a better way to do this. We don't want
    # anything else accidentally changing the lexical order, e.g. web view ordering.
    # But yes, it's ugly. Probably the long-term solution is to make operators dynamic
    # features like predicates, instead of fixed.
    __lexorder = {
        'Assertion': 10, 'Negation': 20, 'Conjunction': 30, 'Disjunction': 40,
        'Material Conditional': 50, 'Material Biconditional': 60, 'Conditional': 70,
        'Biconditional': 80, 'Possibility': 90, 'Necessity': 100,
    }

class Vocabulary(object):
    """
    Create a new vocabulary. *predicate_defs* is a list of tuples (name, index,
    subscript, arity) defining user predicates. Example::

        vocab = Vocabulary([
            ('is tall',        0, 0, 1),
            ('is taller than', 0, 1, 2),
            ('between',        1, 0, 3)
        ])

    """
    def __init__(self, predicate_defs=None):
        # set of predicate instances
        self.user_predicates_set   = set()
        # list of predicate names
        self.user_predicates_list  = []
        # name to predicate instance
        self.user_predicates       = {}
        # string of [subscript, arity] to predicate instance
        self.user_predicates_index = {}
        if predicate_defs:
            for info in predicate_defs:
                if not isinstance(info, list) and not isinstance(info, tuple):
                    raise PredicateError(
                        'predicate_defs must be a list/tuple of lists/tuples.'
                    )
                if len(info) != 4:
                    raise PredicateError(
                        'Predicate declarations must be 4-tuples (name, index, subscript, arity).'
                    )
                self.declare_predicate(*info)

    def copy(self):
        # Shallow copy.
        vocab = Vocabulary()
        vocab.user_predicates = dict(self.user_predicates)
        vocab.user_predicates_list = list(self.user_predicates_list)
        vocab.user_predicates_set = set(self.user_predicates_set)
        vocab.user_predicates_index = dict(self.user_predicates_index)
        return vocab

    def get_predicate(self, name=None, index=None, subscript=None):
        """
        Get a defined predicate, either by name, or by index and subscript. This
        includes system predicates::

            vocab = Vocabulary()
            predicate = vocab.get_predicate('Identity')

        Or user-defined predicates::

            vocab = Vocabulary([('is tall', 0, 0, 1)])
            assert vocab.get_predicate('is tall') == vocab.get_predicate(index=0, subscript=0)

        """
        if name == None and index != None and isinstance(index, basestring):
            name = index
            index = None
        elif index == None and name != None and isinstance(name, int):
            index = name
            name = None
        if name != None:
            if name in system_predicates:
                return system_predicates[name]
            if name in self.user_predicates:
                return self.user_predicates[name]
            raise NoSuchPredicateError(name)
        if index != None and subscript != None:
            idx = str([index, subscript])
            if index < 0:
                if subscript not in system_predicates_index[index]:
                    raise NoSuchPredicateError(idx)
                return system_predicates[system_predicates_index[index][subscript]]
            if idx not in self.user_predicates_index:
                raise NoSuchPredicateError(idx)
            return self.user_predicates_index[idx]
        raise PredicateError('Not enough information to get predicate')

    def declare_predicate(self, name, index, subscript, arity):
        """
        Declare a user-defined predicate::

            vocab = Vocabulary()
            predicate = vocab.declare_predicate(
                name='is tall', index=0, subscript=0, arity=1
            )
            assert predicate == vocab.get_predicate('is tall')
            assert predicate == vocab.get_predicate(index=0, subscript=0)
            
            # predicates cannot be re-declared
            try:
                vocab.declare_predicate('is tall', index=1, subscript=2, arity=3)
            except PredicateAlreadyDeclaredError:
                assert True
            else:
                assert False

        """
        if name in system_predicates:
            raise PredicateAlreadyDeclaredError(
                "Cannot declare system predicate '{0}'".format(name)
            )
        if name in self.user_predicates:
            raise PredicateAlreadyDeclaredError(
                "Predicate '{0}' already declared".format(name)
            )
        try:
            self.get_predicate(index=index, subscript=subscript)
        except NoSuchPredicateError:
            pass
        else:
            raise PredicateAlreadyDeclaredError(
                "Predicate for {0},{1} already declared".format(
                    str(index), str(subscript)
                )
            )
        predicate = Predicate(name, index, subscript, arity)
        self.add_predicate(predicate)
        return predicate

    def add_predicate(self, predicate):
        """
        Add a predicate instance::

            vocab1 = Vocabulary()
            predicate = vocab1.declare_predicate(
                name='is tall', index=0, subscript=0, arity=1
            )
            vocab2 = Vocabulary()
            vocab2.add_predicate(predicate)
            assert vocab2.get_predicate('is tall') == predicate
        """
        if not isinstance(predicate, Predicate):
            raise PredicateError(
                'Predicate must be an instance of Predicate'
            )
        if predicate.index < 0:
            raise PredicateError(
                'Cannot add a system predicate to a vocabulary'
            )
        self.user_predicates[predicate.name] = predicate
        self.user_predicates_index[str([predicate.index, predicate.subscript])] = predicate
        if predicate not in self.user_predicates_set:
            self.user_predicates_set.add(predicate)
            self.user_predicates_list.append(predicate.name)
        return predicate
        
    def list_predicates(self):
        """
        List all predicates in the vocabulary, including system predicates.
        """
        return system_predicates_list + self.user_predicates_list

    def list_user_predicates(self):
        """
        List all predicates in the vocabulary, excluding system predicates.
        """
        return list(self.user_predicates_list)

    @staticmethod
    def _lexrank(*items):
        # Returns the value of __lexorder (below) for the class of each item.
        return (__class__.__lexorder[clas] for clas in (it.__class__ for it in items))

    # Canonical order or all the concrete LexicalItem classes.
    __lexorder = {
        Predicate: 10, Constant: 20, Variable: 30, AtomicSentence: 40,
        PredicatedSentence: 50, QuantifiedSentence: 60, OperatedSentence: 70,
    }

    class Writer(object):

        # Base sentence writer, implemented by notations.

        # TODO: cleanup sentence writer, proof writer, parser, symbol set design b.s.

        symbol_sets = {}
        symbol_set = None

        def __init__(self, symbol_set = None):
            self.symbol_set = self.symset(symbol_set)

        def symset(self, symbol_set = None):
            if symbol_set == None:
                if self.symbol_set == None:
                    symbol_set = 'default'
                else:
                    # could have been set by manually after init
                    symbol_set = self.symbol_set
            if isinstance(symbol_set, basestring):
                return self.symbol_sets[symbol_set]
            else:
                return symbol_set

        def write(self, sentence, symbol_set = None, **opts):
            if sentence.is_atomic():
                return self.write_atomic(sentence, symbol_set = symbol_set)
            elif sentence.is_quantified():
                return self.write_quantified(sentence, symbol_set = symbol_set)
            elif sentence.is_predicated():
                return self.write_predicated(sentence, symbol_set = symbol_set)
            elif sentence.is_operated():
                return self.write_operated(sentence, symbol_set = symbol_set)
            else:
                raise NotImplementedError()

        def write_atomic(self, sentence, symbol_set = None):
            symset = self.symset(symbol_set)
            return symset.charof('atomic', sentence.index) + self.write_subscript(
                sentence.subscript, symbol_set = symbol_set
            )

        def write_quantified(self, sentence, symbol_set = None):
            symset = self.symset(symbol_set)
            return ''.join([
                symset.charof('quantifier', sentence.quantifier),
                symset.charof('variable', sentence.variable.index),
                self.write_subscript(sentence.variable.subscript, symbol_set = symbol_set),
                self.write(sentence.sentence, symbol_set = symbol_set)
            ])

        def write_predicated(self, sentence, symbol_set = None):
            symset = self.symset(symbol_set)
            s = self.write_predicate(sentence.predicate, symbol_set = symbol_set)
            for param in sentence.parameters:
                s += self.write_parameter(param, symbol_set = symbol_set)
            return s

        def write_operated(self, sentence, symbol_set = None):
            raise NotImplementedError()

        def write_operator(self, operator, symbol_set = None):
            symset = self.symset(symbol_set)
            return symset.charof('operator', operator)

        def write_predicate(self, predicate, symbol_set = None):
            symset = self.symset(symbol_set)
            if predicate.name in system_predicates:
                s = symset.charof('system_predicate', predicate.name)
            else:
                s = symset.charof('user_predicate', predicate.index)
            s += self.write_subscript(predicate.subscript, symbol_set = symbol_set)
            return s

        def write_parameter(self, param, symbol_set = None):
            if param.is_constant():
                return self.write_constant(param, symbol_set = symbol_set)
            elif param.is_variable():
                return self.write_variable(param, symbol_set = symbol_set)
            else:
                raise NotImplementedError()

        def write_constant(self, constant, symbol_set = None):
            symset = self.symset(symbol_set)
            return ''.join([
                symset.charof('constant', constant.index),
                self.write_subscript(constant.subscript, symbol_set = symbol_set)
            ])

        def write_variable(self, variable, symbol_set = None):
            symset = self.symset(symbol_set)
            return ''.join([
                symset.charof('variable', variable.index),
                self.write_subscript(variable.subscript, symbol_set = symbol_set)
            ])

        def write_subscript(self, subscript, symbol_set = None):
            symset = self.symset(symbol_set)
            if symset.name == 'html':
                if subscript != 0:
                    return ''.join([
                        '<span class="subscript">',
                        symset.subfor(subscript, skip_zero = True),
                        '</span>'
                    ])
                return ''
            else:
                return symset.subfor(subscript, skip_zero = True)

system_predicates = {
    'Identity'  : Predicate('Identity',  -1, 0, 2),
    'Existence' : Predicate('Existence', -2, 0, 1),
}

def get_system_predicate(name):
    return system_predicates[name]