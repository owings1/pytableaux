from errors import ParseError, IllegalStateError, NotFoundError, \
    UnboundVariableError, BoundVariableError
from lexicals import Argument, AtomicSentence, PredicatedSentence, get_system_predicate, \
    QuantifiedSentence, OperatedSentence, Constant, Variable, operators, Vocabulary
from fixed import default_notation
from utils import isstr, SymbolSet
from past.builtins import basestring

def parse(input, *args, **kw):
    """
    Parse a string and return a sentence.
    Convenience wrapper for ``create_parser().parse()``.

    :rtype: Sentence
    """
    return create_parser(*args, **kw).parse(input)

def parse_argument(conclusion, premises=None, title=None, **kw):
    """
    Parse conclusion, and optional premises, and return an argument.
    Convenience wrapper for ``create_parser().parse_argument()``.

    :rtype: Argument
    """
    return create_parser(**kw).argument(conclusion, premises, title)

def create_parser(notn=None, vocab=None, **opts):
    """
    Create a sentence parser with the given spec. This is
    useful if you parsing many sentences with the same notation
    and vocabulary.

    :param str notn: The parser notation. Uses the default notation
        if not passed.
    :param Vocabulary vocab: The vocabulary instance containing any
        custom predicate definitions. If not passed, a new instance is
        created.
    :return: The parser instance
    :rtype: Parser
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
    raise ValueError('Unknown parser: {0}'.format(str(notn)))

class Parser(object):
    def parse(self, input):
        """
        Parse a sentence from an input string.

        :param str input: The input string.
        :return: The parsed sentence.
        :rtype: Sentence
        :raises errors.ParseError:
        """
        raise NotImplementedError()
    def argument(self, conclusion, premises=None, title=None):
        raise NotImplementedError()

class BaseParser(Parser):

    # The base ``Parser`` class handles parsing operations common to both Polish
    # and standard notation. This consists of all parsing except for operator
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

    def parse(self, input):
        with self.__state:
            self.s = list(input)
            self.pos = 0
            self._chomp()
            if not self._has_current():
                raise ParseError('Input cannot be empty.')
            s = self._read()
            self._chomp()
            if self._has_current():
                raise ParseError(
                    "Unexpected character '{0}' at position {1}.".format(self._current(), self.pos)
                )
        return s

    def argument(self, conclusion, premises=None, title=None):
        """
        Parse the input strings and create an argument.

        :param str conclusion: The argument's conclusion.
        :param list premises: List of premise strings, if any.
        :param str title: The title to pass to the argument's constructor.
        :return: The argument.
        :rtype: argument
        :raises Parser.ParseError:
        """
        if isstr(conclusion):
            conc = self.parse(conclusion)
        else:
            conc = conclusion
        prems = []
        if premises:
            for s in premises:
                prems.append(self.parse(s) if isstr(s) else s)
        return Argument(
            conclusion = conc, premises = prems, title = title
        )

    ## ==========================================
    ##  Medium-level parsing methods - Sentences
    ## ==========================================

    def _read(self):
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
        ctype = self._assert_current()
        if ctype == 'user_predicate' or ctype == 'system_predicate':
            s = self._read_predicate_sentence()
        elif ctype == 'quantifier':
            s = self._read_quantified_sentence()
        elif ctype == 'atomic':
            s = self._read_atomic()
        else:
            raise ParseError(
                "Unexpected {0} '{1}' at position {2}.".format(ctype, self._current(), self.pos)
            )
        return s

    def _read_atomic(self):
        """
        Read an atomic sentence starting from the current character.

        :rtype: Vocabulary.AtomicSentence
        :meta private:
        """
        return AtomicSentence(**self._read_item())

    def _read_predicate_sentence(self):
        """
        Read predicated sentence starting from the current character.

        :rtype: Vocabulary.PredicatedSentence
        :meta private:
        """
        predicate = self._read_predicate()
        params = self._read_parameters(predicate.arity)
        return PredicatedSentence(predicate, params)

    def _read_quantified_sentence(self):
        """
        Read quantified sentence starting from the current character.

        :rtype: Vocabulary.PredicatedSentence
        :meta private:
        """
        self._assert_current_is('quantifier')
        quantifier = self.symbol_set.indexof('quantifier', self._current())
        self._advance()
        v = self._read_variable()
        if v in list(self.bound_vars):
            var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
            raise BoundVariableError(
                "Cannot rebind variable '{0}' at position {1}.".format(var_str, self.pos)
            )
        self.bound_vars.add(v)
        sentence = self._read()
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

    def _read_predicate(self):
        """
        Read a predicate starting from the current character.

        :rtype: Vocabulary.Predicate
        :meta private:
        """
        pchar = self._current()
        cpos = self.pos
        ctype = self._typeof(pchar)
        if ctype == 'system_predicate':
            name = self.symbol_set.indexof(ctype, pchar)
            self._advance()
            return get_system_predicate(name)
        try:
            return self.vocab.get_predicate(**self._read_item())
        except NotFoundError:
            raise ParseError(
                "Undefined predicate symbol '{0}' at position {1}.".format(pchar, cpos)
            )

    def _read_parameters(self, num):
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
            parameters.append(self._read_parameter())
        return parameters

    def _read_parameter(self):
        """
        Read a single parameter (constant or variable) from the current character.

        :rtype: Vocabulary.Parameter
        :raises Parser.UnboundVariableError: if a variable appears that has not
            been bound by a quantifier.
        :meta private:
        """
        ctype = self._assert_current_is('constant', 'variable')
        if ctype == 'constant':
            return self._read_constant()
        else:
            cpos = self.pos
            v = self._read_variable()
            if v not in list(self.bound_vars):
                var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
                raise UnboundVariableError(
                    "Unbound variable '{0}' at position {1}.".format(var_str, cpos)
                )
            return v

    def _read_variable(self):
        """
        Read a variable starting from the current character.

        :rtype: Vocabulary.Variable
        :meta private:
        """
        return Variable(**self._read_item())

    def _read_constant(self):
        """
        Read a constant starting from the current character.

        :rtype: Vocabulary.Constant
        :meta private:
        """
        return Constant(**self._read_item())

    def _read_subscript(self):
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
        while self._current() and self._typeof(self._current()) == 'digit':
            sub.append(self._current())
            self._advance()
        if not len(sub):
            sub.append('0')
        return int(''.join(sub))

    def _read_item(self, ctype = None):
        """
        Read an item and its subscript starting from the current character,
        which must be in the list of characters given. Returns a dict with
        keys `index` and `subscript`, where `index` is the list index in
        the symbol set. This is a generic way to read user predicates,
        atomics, variables, constants, etc. Note, this will not work for
        system predicates, because they have string keys in the symbols set.

        :rtype: dict
        :meta private:
        """
        if ctype == None:
            ctype = self._typeof(self._current())
        else:
            self._assert_current_is(ctype)
        index = self.symbol_set.indexof(ctype, self._current())
        self._advance()
        subscript = self._read_subscript()
        return {'index': index, 'subscript': subscript}

    ## ============================
    ##  Low-level parsing methods
    ## ============================

    def _current(self):
        # Get the current character, or ``None`` if after last.
        return self._next(0)

    def _assert_current(self):
        # Raise a ``ParseError`` if after last.
        if not self._has_current():
            raise ParseError(
                'Unexpected end of input at position {0}.'.format(self.pos)
            )
        return self._typeof(self._current())

    def _assert_current_is(self, *ctypes):
        ctype = self._assert_current()
        if ctype not in ctypes:
            raise ParseError(
                "Unexpected {0} '{1}' at position {2}.".format(ctype, self._current(), self.pos)
            )
        return ctype

    def _has_next(self, n=1):
        # Check whether there are n-many characters after the current.
        self.__state.check_started()
        return (len(self.s) > self.pos + n)

    def _has_current(self):
        # check whether there is a current character, or return ``False``` if after last.
        return self._has_next(0)

    def _next(self, n=1):
        # Get the nth character after the current, of ``None``` if ``n``` is after last.
        if self._has_next(n):
            return self.s[self.pos+n]
        return None

    def _advance(self, n=1):
        # Advance the current pointer n-many characters, and then eat whitespace.
        self.__state.check_started()
        self.pos += n  
        self._chomp()
        return self

    def _chomp(self):
        # Proceeed through whitepsace.
        while self._has_current() and self._typeof(self._current()) == 'whitespace':
            self.pos += 1
        return self

    def _typeof(self, c):
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
                raise IllegalStateError(
                    'Parser is already parsing -- not thread safe'
                )
            self.inst.bound_vars = set()
            self.is_parsing = True

        def __exit__(self, type, value, traceback):
            self.is_parsing = False
            self.inst.bound_vars = set()

class PolishParser(BaseParser):

    symbol_set = SymbolSet('polish.ascii')

    def _read(self):
        ctype = self._assert_current()
        if ctype == 'operator':
            operator = self.symbol_set.indexof('operator', self._current())
            self._advance()
            operands = [self._read() for x in range(operators[operator])]
            s = OperatedSentence(operator, operands)
        else:
            s = super()._read()
        return s

class StandardParser(BaseParser):

    symbol_set = SymbolSet('standard.ascii')

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

    def _read(self):
        # override
        ctype = self._assert_current()
        if ctype == 'operator':
            s = self.__read_operator_sentence()
        elif ctype == 'paren_open':
            s = self.__read_from_open_paren()
        elif ctype == 'variable' or ctype == 'constant':
            s = self.__read_infix_predicate_sentence()
        else:
            s = super()._read()
        return s

    def __read_operator_sentence(self):
        operator = self.symbol_set.indexof('operator', self._current())
        arity = operators[operator]
        # only unary operators can be prefix operators
        if arity != 1:
            raise ParseError(
                "Unexpected non-prefix operator symbol '{0}' at position {1}.".format(
                    self._current(), self.pos
                )
            )
        self._advance()
        operand = self._read()
        return OperatedSentence(operator, [operand])

    def __read_infix_predicate_sentence(self):
        params = [self._read_parameter()]
        self._assert_current_is('user_predicate', 'system_predicate')
        ppos = self.pos
        predicate = self._read_predicate()
        if predicate.arity < 2:
            raise ParseError(
                "Unexpected {0}-ary predicate at position {1}. Infix notation requires arity > 1.".format(predicate.arity, ppos))
        params += self._read_parameters(predicate.arity - 1)
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
            if not self._has_next(length):
                raise ParseError(
                    'Unterminated open parenthesis at position {0}.'.format(self.pos)
                )
            peek = self._next(length)
            ptype = self._typeof(peek)
            if ptype == 'paren_close':
                depth -= 1
            elif ptype == 'paren_open':
                depth += 1
            elif ptype == 'operator':
                peek_operator = self.symbol_set.indexof('operator', peek)
                if operators[peek_operator] == 2 and depth == 1:
                    if operator != None:
                        raise ParseError(
                            'Unexpected binary operator at position {0}.'.format(self.pos + length)
                        )
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
        self._advance()
        # read the lhs
        lhs = self._read()
        self._chomp()
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
        self._advance()
        # read the rhs
        rhs = self._read()
        self._chomp()
        # now we should have a close paren
        self._assert_current_is('paren_close')
        # move past the close paren
        self._advance()
        return OperatedSentence(operator, [lhs, rhs])