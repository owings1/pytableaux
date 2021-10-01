from errors import ParseError, ParserThreadError, IllegalStateError, \
    UnboundVariableError, BoundVariableError, NoSuchPredicateError, UnknownNotationError
from lexicals import Argument, AtomicSentence, PredicatedSentence, \
    QuantifiedSentence, OperatedSentence, Constant, Variable, operators, Vocabulary
from fixed import default_notation
from utils import SymbolSet
from past.builtins import basestring

def create_parser(notn=None, vocab=None, **opts):
    """
    TODO: doc
    """
    if isinstance(notn, Vocabulary) or isinstance(vocab, basestring):
        # Accept inverted args for backwards compatibility.
        notn, vocab = (vocab, notn)
    if not vocab:
        vocab = Vocabulary()
    if not notn:
        notn = default_notation
    if notn == 'polish':
        return PolishParser(vocab, **opts)
    elif notn == 'standard':
        return StandardParser(vocab, **opts)
    raise UnknownNotationError('Unknown parser: {0}'.format(str(notn)))

def parse(input, *args, **kw):
    """
    Convenience wrapper for ``create_parser().parse()``.
    """
    return create_parser(*args, **kw).parse(input)

class BaseParser(object):

    # The base ``Parser`` class handles parsing operations common to all notations
    # (Polish and Standard). This consists of all parsing except for operator
    # expressions, as well as the following classes of symbols:
    # 
    # - Whitespace symbols: the *space* character.
    # - Subscript symbols: digit characters.
    # 
    # Each specific notation defines its own characters for each of the following
    # classes of symbols:
    # 
    # - Constant symbols
    # - Variable symbols
    # - Predicate symbols, including system-defined predicates, and user-defined
    #   predicates.
    # - Quantifier symbols
    # - Operator symbols
    # - Atomic sentence (proposition) symbols
    def __init__(self, vocab, **opts):
        self.vocab = vocab
        self.opts = opts
        self.__state = self.__State(self)

    def parse(self, string):
        """
        Parse a sentence from an input string.

        :param str string: The input string.
        :return: The parsed sentence.
        :rtype: Vocabulary.Sentence
        :raises Parser.ParseError:
        """
        with self.__state:
            self.s   = list(string)
            self.pos = 0
            self.chomp()
            if not self.has_current():
                raise ParseError('Input cannot be empty.')
            s = self.read()
            self.chomp()
            if self.has_current():
                raise ParseError(
                    "Unexpected character '{0}' at position {1}.".format(self.current(), self.pos)
                )
        return s

    def argument(self, conclusion=None, premises=[], title=None):
        """
        Parse the input strings and create an argument.

        :param str conclusion: The argument's conclusion.
        :param list premises: List of premise strings, if any.
        :param str title: The title to pass to the argument's constructor.
        :return: The argument.
        :rtype: argument
        :raises Parser.ParseError:
        """
        return Argument(
            conclusion = self.parse(conclusion),
            premises = [self.parse(s) for s in premises],
            title = title
        )

    ## ==========================================
    ##  Medium-level parsing methods - Sentences
    ## ==========================================

    def read(self):
        """
        Internal entrypoint for reading a sentence. Implementation is recursive.
        This provides the default implementation for prefix notation sentences,
        i.e. atomic, predicated, and quantified sentences.

        This does not parse operated sentences, Subclasses *must* override
        this method, and delegate to ``super()`` for the default implementation
        when appropriate.

        :rtype: Vocabulary.Sentence
        :meta private:
        :raises Parser.ParseError:
        """
        ctype = self.assert_current()
        if ctype == 'user_predicate' or ctype == 'system_predicate':
            s = self.read_predicate_sentence()
        elif ctype == 'quantifier':
            s = self.read_quantified_sentence()
        elif ctype == 'atomic':
            s = self.read_atomic()
        else:
            raise ParseError(
                "Unexpected {0} '{1}' at position {2}.".format(ctype, self.current(), self.pos)
            )
        return s

    def read_atomic(self):
        """
        Read an atomic sentence starting from the current character.

        :rtype: Vocabulary.AtomicSentence
        :meta private:
        """
        return AtomicSentence(**self.read_item())

    def read_predicate_sentence(self):
        """
        Read predicated sentence starting from the current character.

        :rtype: Vocabulary.PredicatedSentence
        :meta private:
        """
        predicate = self.read_predicate()
        params = self.read_parameters(predicate.arity)
        return PredicatedSentence(predicate, params)

    def read_quantified_sentence(self):
        """
        Read quantified sentence starting from the current character.

        :rtype: Vocabulary.PredicatedSentence
        :meta private:
        """
        self.assert_current_is('quantifier')
        quantifier = self.symbol_set.indexof('quantifier', self.current())
        self.advance()
        v = self.read_variable()
        if v in list(self.bound_vars):
            var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
            raise BoundVariableError(
                "Cannot rebind variable '{0}' at position {1}.".format(var_str, self.pos)
            )
        self.bound_vars.add(v)
        sentence = self.read()
        if v not in list(sentence.variables()):
            var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
            raise BoundVariableError(
                "Unused bound variable '{0}' at position {1}.".format(var_str, self.pos)
            )
        self.bound_vars.remove(v)
        return QuantifiedSentence(quantifier, v, sentence)

    ## ==========================================
    ##  Medium-level parsing methods - Parameters
    ## ==========================================

    def read_predicate(self):
        """
        Read a predicate starting from the current character.

        :rtype: Vocabulary.Predicate
        :meta private:
        """
        pchar = self.current()
        cpos = self.pos
        try:
            return self.vocab.get_predicate(**self.read_item())
        except NoSuchPredicateError:
            raise ParseError(
                "Undefined predicate symbol '{0}' at position {1}.".format(pchar, cpos)
            )

    def read_parameters(self, num):
        """
        Read the given number of parameters (constants or variables) starting
        from the current character.

        :param int num: The number of parameters to read, which should equal the
            predicate's arity.
        :return: A list of `Vocabulary.Parameter` objects.
        :rtype: list
        :meta private:
        """
        parameters = []
        while len(parameters) < num:
            parameters.append(self.read_parameter())
        return parameters

    def read_parameter(self):
        """
        Read a single parameter (constant or variable) from the current character.

        :rtype: Vocabulary.Parameter
        :raises Parser.UnboundVariableError: if a variable appears that has not
            been bound by a quantifier.
        :meta private:
        """
        ctype = self.assert_current_is('constant', 'variable')
        if ctype == 'constant':
            return self.read_constant()
        else:
            cpos = self.pos
            v = self.read_variable()
            if v not in list(self.bound_vars):
                var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
                raise UnboundVariableError(
                    "Unbound variable '{0}' at position {1}.".format(var_str, cpos)
                )
            return v

    def read_variable(self):
        """
        Read a variable starting from the current character.

        :rtype: Vocabulary.Variable
        :meta private:
        """
        return Variable(**self.read_item())

    def read_constant(self):
        """
        Read a constant starting from the current character.

        :rtype: Vocabulary.Constant
        :meta private:
        """
        return Constant(**self.read_item())

    def read_subscript(self):
        """
        Read the subscript starting from the current character. If the current
        character is not a digit, or we are after last, then the subscript is
        ``0```. Otherwise, all consecutive digit characters are read
        (whitespace allowed), and then converted to an integer, which is then
        returned.

        :rtype: int
        :meta private:
        """
        sub = []
        while self.current() and self.typeof(self.current()) == 'digit':
            sub.append(self.current())
            self.advance()
        if not len(sub):
            sub.append('0')
        return int(''.join(sub))

    def read_item(self, ctype = None):
        """
        Read an item and its subscript starting from the current character,
        which must be in the list of characters given. Returns a list containing
        the index of the current character in the chars list, and the subscript
        of that item. This is a generic way to read predicates, atomics, variables,
        constants, etc.

        :rtype: dict
        :meta private:
        """
        if ctype == None:
            ctype = self.typeof(self.current())
        else:
            self.assert_current_is(ctype)
        index = self.symbol_set.indexof(ctype, self.current())
        self.advance()
        subscript = self.read_subscript()
        return {'index': index, 'subscript': subscript}

    ## ============================
    ##  Low-level parsing methods
    ## ============================

    def current(self):
        # Get the current character, or ``None`` if after last.
        return self.next(0)

    def assert_current(self):
        # Raise a ``ParseError`` if after last.
        if not self.has_current():
            raise ParseError(
                'Unexpected end of input at position {0}.'.format(self.pos)
            )
        return self.typeof(self.current())

    def assert_current_is(self, *ctypes):
        self.assert_current()
        ctype = self.typeof(self.current())
        if ctype not in ctypes:
            raise ParseError(
                "Unexpected {0} '{1}' at position {2}.".format(ctype, self.current(), self.pos)
            )
        return ctype

    def has_next(self, n=1):
        # Check whether there are n-many characters after the current.
        self.__state.check_started()
        return (len(self.s) > self.pos + n)

    def has_current(self):
        # check whether there is a current character, or return ``False``` if after last.
        return self.has_next(0)

    def next(self, n=1):
        # Get the nth character after the current, of ``None``` if ``n``` is after last.
        if self.has_next(n):
            return self.s[self.pos+n]
        return None

    def advance(self, n=1):
        # Advance the current pointer n-many characters, and then eat whitespace.
        self.__state.check_started()
        self.pos += n  
        self.chomp()
        return self

    def chomp(self):
        # Proceeed through whitepsace.
        while self.has_current() and self.typeof(self.current()) == 'whitespace':
            self.pos += 1
        return self

    def typeof(self, c):
        return self.symbol_set.typeof(c)

    class __State(object):

        def __init__(self, inst):
            self.inst = inst
            self.is_parsing = False

        def check_started(self):
            if not self.is_parsing:
                raise IllegalStateError(
                    'Illegal method call -- not parsing'
                )
        def __enter__(self):
            if self.is_parsing:
                raise ParserThreadError(
                    'Parser is already parsing -- not thread safe'
                )
            self.inst.bound_vars = set()
            self.is_parsing = True

        def __exit__(self, type, value, traceback):
            self.is_parsing = False
            self.inst.bound_vars = set()

class PolishParser(BaseParser):

    symbol_set = SymbolSet('polish', 'ascii')

    def read(self):
        ctype = self.assert_current()
        if ctype == 'operator':
            operator = self.symbol_set.indexof('operator', self.current())
            self.advance()
            operands = [self.read() for x in range(operators[operator])]
            s = OperatedSentence(operator, operands)
        else:
            s = super().read()
        return s

class StandardParser(BaseParser):

    symbol_set = SymbolSet('standard', 'ascii')

    def parse(self, string):
        # override
        try:
            s = super().parse(string)
        except ParseError as e:
            try:
                # allow dropped outer parens
                pstring = ''.join([
                    self.symbol_set.charof('paren_open', 0),
                    string,
                    self.symbol_set.charof('paren_close', 0)
                ])
                s = super().parse(pstring)
            except ParseError as e1:
                raise e
            else:
                return s
        else:
            return s

    def read(self):
        # override
        ctype = self.assert_current()
        if ctype == 'operator':
            s = self.__read_operator_sentence()
        elif ctype == 'paren_open':
            s = self.__read_from_open_paren()
        elif ctype == 'variable' or ctype == 'constant':
            s = self.__read_infix_predicate_sentence()
        else:
            s = super().read()
        return s

    def __read_operator_sentence(self):
        operator = self.symbol_set.indexof('operator', self.current())
        arity = operators[operator]
        # only unary operators can be prefix operators
        if arity != 1:
            raise ParseError(
                "Unexpected non-prefix operator symbol '{0}' at position {1}.".format(
                    self.current(), self.pos
                )
            )
        self.advance()
        operand = self.read()
        return OperatedSentence(operator, [operand])

    def __read_infix_predicate_sentence(self):
        params = [self.read_parameter()]
        self.assert_current_is('user_predicate', 'system_predicate')
        ppos = self.pos
        predicate = self.read_predicate()
        if predicate.arity < 2:
            raise ParseError(
                "Unexpected {0}-ary predicate at position {1}. Infix notation requires arity > 1.".format(predicate.arity, ppos))
        params += self.read_parameters(predicate.arity - 1)
        return PredicatedSentence(predicate, params)

    def __read_from_open_paren(self):
        # if we have an open parenthesis, then we demand a binary infix operator sentence.
        # scan ahead to:
        #   - find the corresponding close parenthesis position
        #   - find the binary operator and its position
        operator = None
        operator_pos = None
        depth = 1
        length = 1
        while depth:
            if not self.has_next(length):
                raise ParseError('Unterminated open parenthesis at position {0}.'.format(self.pos))
            peek = self.next(length)
            ptype = self.typeof(peek)
            if ptype == 'paren_close':
                depth -= 1
            elif ptype == 'paren_open':
                depth += 1
            elif ptype == 'operator':
                peek_operator = self.symbol_set.indexof('operator', peek)
                if operators[peek_operator] == 2 and depth == 1:
                    if operator != None:
                        raise ParseError('Unexpected binary operator at position {0}.'.format(self.pos + length))
                    operator_pos = self.pos + length
                    operator = peek_operator
            length += 1
        if operator == None:
            raise ParseError('Parenthetical expression is missing binary operator at position {0}.'.format(self.pos))
        #if length == 2: #if length == 1:
        #    raise logic.Parser.ParseError('Empty parenthetical expression at position {0}.'.format(self.pos))
        # now we can divide the string into lhs and rhs
        lhs_start = self.pos + 1
        # move past the open paren
        self.advance()
        # read the lhs
        lhs = self.read()
        self.chomp()
        if self.pos != operator_pos:
            raise ParseError(
                ''.join([
                    'Invalid left side expression starting at position {0} and ending at position {1},',
                    'which proceeds past operator ({2}) at position {3}.'
                ]).format(
                    lhs_start, self.pos, operator, operator_pos
                )
            )
        # move past the operator
        self.advance()
        # read the rhs
        rhs = self.read()
        self.chomp()
        # now we should have a close paren
        self.assert_current_is('paren_close')
        # move past the close paren
        self.advance()
        return OperatedSentence(operator, [lhs, rhs])