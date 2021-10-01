from fixed import num_atomic_symbols, num_const_symbols, num_predicate_symbols, \
    num_var_symbols, operators, system_predicates_index, system_predicates_list, \
    default_notation, quantifiers

from errors import PredicateError, IndexTooLargeError, PredicateArityError, \
    PredicateSubscriptError, PredicateAlreadyDeclaredError, NoSuchPredicateError, \
    PredicateArityMismatchError, NoSuchOperatorError, OperatorArityMismatchError, \
    BadArgumentError

from utils import cat, SymbolSet

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
        r1, r2 = LexicalItem._lexrank(self, other)
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

    def __repr__(self):
        """
        Default representation with lex-order + sort-tuple.
        """
        return (LexicalItem.__lexorder[self.__class__], self.sort_tuple()).__repr__()

    @staticmethod
    def _lexrank(*items):
        # Returns the value of __lexorder (below) for the class of each item.
        return tuple(LexicalItem.__lexorder[clas] for clas in (it.__class__ for it in items))

    @staticmethod
    def _initorder():
        # Canonical order or all the concrete LexicalItem classes.
        LexicalItem.__lexorder = {
            Predicate: 10, Constant: 20, Variable: 30, AtomicSentence: 40,
            PredicatedSentence: 50, QuantifiedSentence: 60, OperatedSentence: 70,
            # Abstract, just a safety measure
            Parameter: 416, Sentence: 417, LexicalItem: 418,
        }
        # This method self-destucts.
        delattr(LexicalItem, '_initorder')

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

    def is_negated(self):
        """
        TODO: doc
        """
        return isinstance(self, OperatedSentence) and self.operator == 'Negation'

    def substitute(self, new_param, old_param):
        """
        Recursively substitute ``new_param`` for all occurrences of ``old_param``.
        May return self, or a new sentence.
        """
        raise NotImplementedError()

    def negate(self):
        """
        Convenience method to negate the sentence.
        """
        return OperatedSentence('Negation', [self])

    def negative(self):
        """
        TODO: doc
        """
        return self.negatum if self.is_negated() else self.negate()

    def asserted(self):
        """
        TODO: doc
        """
        return OperatedSentence('Assertion', [self])

    def disjoin(self, rhs):
        """
        TODO: doc
        """
        return OperatedSentence('Disjunction', [self, rhs])

    def conjoin(self, rhs):
        """
        TODO: doc
        """
        return OperatedSentence('Conjunction', [self, rhs])

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

# Initialize order.
LexicalItem._initorder()

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

class Argument(object):
    """
    Create an argument from sentence objects. For parsing strings into arguments,
    see ``Parser.argument``.
    """
    def __init__(self, conclusion, premises=None, title=None):
        self.premises = []
        if premises:
            for premise in premises:
                if not isinstance(premise, Sentence):
                    raise TypeError('premises must be Sentence objects')
                self.premises.append(premise)
        if not isinstance(conclusion, Sentence):
            raise TypeError('conclusion must be Sentence object')
        self.conclusion = conclusion
        self.title      = title

    def __repr__(self):
        if self.title is None:
            return [self.premises, self.conclusion].__repr__()
        return [self.premises, self.conclusion, {'title': self.title}].__repr__()

    def __hash__(self):
        return hash((self.conclusion,) + tuple(self.premises))

    def __eq__(self, other):
        """
        Two arguments are considered equal just when their conclusions are equal, and their
        premises are equal (and in the same order) The title is not considered in equality.
        """
        return isinstance(other, self.__class__) and hash(self) == hash(other)

    def __ne__(self, other):
        return not isinstance(other, self.__class__) or hash(self) != hash(other)

def create_lexwriter(notn=None, format=None, **opts):
    if not notn:
        notn = default_notation
    if not format:
        format = 'ascii'
    symbol_set = SymbolSet(notn, format)
    if notn == 'polish':
        return PolishLexWriter(symbol_set, **opts)
    if notn == 'standard':
        return StandardLexWriter(symbol_set, **opts)
    raise BadArgumentError('Invalid notation: {0}'.format(str(notn)))

class BaseLexWriter(object):

    # Base lex writer.

    def __init__(self, symbol_set, **opts):
        self.symbol_set = symbol_set
        self.format = symbol_set.name
        self.opts = opts

    def write(self, item):
        if isinstance(item, basestring):
            if item in operators:
                return self.write_operator(item)
            if item in quantifiers:
                return self.write_quantifier(item)
            raise TypeError('Unknown lexical type: {0}'.format(item))
        if isinstance(item, Parameter):
            return self.write_parameter(item)
        if isinstance(item, Predicate):
            return self.write_sentence(item)
        if isinstance(item, Sentence):
            return self.write_sentence(item)
        raise TypeError('Unknown lexical type: {0}'.format(item))

    def write_operator(self, operator):
        return self.charof('operator', operator)

    def write_quantifier(self, quantifier):
        return self.charof('quantifier', quantifier)

    def write_parameter(self, param):
        if param.is_constant():
            return self.write_constant(param)
        if param.is_variable():
            return self.write_variable(param)
        raise TypeError('Unknown lexical type: {0}'.format(str(param)))

    def write_constant(self, constant):
        return cat(
            self.charof('constant', constant.index),
            self.write_subscript(constant.subscript),
        )

    def write_variable(self, variable):
        return cat(
            self.charof('variable', variable.index),
            self.write_subscript(variable.subscript),
        )

    def write_predicate(self, predicate):
        if predicate.name in system_predicates:
            typ, key = ('system_predicate', predicate.name)
        else:
            typ, key = ('user_predicate', predicate.index)
        return cat(
            self.charof(typ, key),
            self.write_subscript(predicate.subscript),
        )

    def write_sentence(self, sentence):
        if sentence.is_atomic():
            return self.write_atomic(sentence)
        if sentence.is_predicated():
            return self.write_predicated(sentence)
        if sentence.is_quantified():
            return self.write_quantified(sentence)
        if sentence.is_operated():
            return self.write_operated(sentence)
        raise TypeError('Unknown sentence type: {0}'.format(str(sentence)))

    def write_atomic(self, sentence):
        return cat(
            self.charof('atomic', sentence.index),
            self.write_subscript(sentence.subscript)
        )

    def write_quantified(self, sentence):
        return ''.join([
            self.write_quantifier(sentence.quantifier),
            self.write_variable(sentence.variable),
            self.write_sentence(sentence.sentence),
        ])

    def write_predicated(self, sentence):
        s = self.write_predicate(sentence.predicate)
        for param in sentence.parameters:
            s += self.write_parameter(param)
        return s

    def write_operated(self, sentence):
        raise NotImplementedError()

    def charof(self, *args, **kw):
        return self.symbol_set.charof(*args, **kw)

    def write_subscript(self, subscript):
        symset = self.symbol_set
        if self.format == 'html':
            if subscript != 0:
                return ''.join([
                    '<span class="subscript">',
                    symset.subfor(subscript, skip_zero = True),
                    '</span>'
                ])
            return ''
        else:
            return symset.subfor(subscript, skip_zero = True)

class PolishLexWriter(BaseLexWriter):

    def write_operated(self, sentence):
        return cat(
            self.write_operator(sentence.operator),
            *(self.write_sentence(s) for s in sentence.operands),
        )

class StandardLexWriter(BaseLexWriter):

    __defaults = {'drop_parens': True}

    def __init__(self, *args, **kw):
        super().__init__(*args, **self.__defaults, **kw)
        opts = self.opts
        self.drop_parens = bool(opts['drop_parens'])

    def write(self, item):
        if self.drop_parens and isinstance(item, OperatedSentence):
            return self.write_operated(item, drop_parens = True)
        return super().write(item)

    def write_predicated(self, sentence):
        # Infix notation for predicates of arity > 1
        if sentence.predicate.arity < 2:
            return super().write_predicated(sentence)
        # For Identity, add spaces (a = b instead of a=b)
        ws = self.charof('whitespace', 0) if sentence.predicate.name == 'Identity' else ''
        return cat(
            self.write_parameter(sentence.parameters[0]),
            ws,
            self.write_predicate(sentence.predicate),
            ws,
            *(self.write_parameter(param) for param in sentence.parameters[1:]),
        )

    def write_operated(self, sentence, drop_parens = False):
        oper = sentence.operator
        arity = operators[oper]
        if arity == 1:
            operand = sentence.operand
            if (self.format == 'html' and
                oper == 'Negation' and
                operand.is_predicated() and
                operand.predicate.name == 'Identity'):
                return self.__write_html_negated_identity(sentence)
            else:
                return self.write_operator(oper) + self.write(operand)
        elif arity == 2:
            return ''.join([
                self.charof('paren_open', 0) if not drop_parens else '',
                self.charof('whitespace', 0).join([
                    self.write(sentence.lhs),
                    self.write_operator(oper),
                    self.write(sentence.rhs),
                ]),
                self.charof('paren_close', 0) if not drop_parens else '',
            ])
        raise NotImplementedError('No support for operators of arity {0}'.format(str(arity)))

    def __write_html_negated_identity(self, sentence):
        params = sentence.operand.parameters
        return cat(
            self.write_parameter(params[0]),
            self.charof('whitespace', 0),
            self.charof('system_predicate', 'NegatedIdentity'),
            self.charof('whitespace', 0),
            self.write_parameter(params[1]),
        )

system_predicates = {
    'Identity'  : Predicate('Identity',  -1, 0, 2),
    'Existence' : Predicate('Existence', -2, 0, 1),
}

def get_system_predicate(name):
    """
    TODO: doc
    """
    return system_predicates[name]

def operarity(oper):
    """
    TODO: doc
    """
    return operators[oper]

# Shorthand

Atomic = AtomicSentence
Predicated = PredicatedSentence
Operated = OperatedSentence
Quantified = QuantifiedSentence
