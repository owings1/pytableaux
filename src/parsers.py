from errors import ParseError, BoundVariableError, UnboundVariableError, \
    IllegalStateError, NotFoundError
from lexicals import Constant, Variable,  Atomic, Predicated, Quantified, \
    Operated, Vocabulary, Argument, get_system_predicate, operarity
    
from utils import cat, isstr

notations = ('polish', 'standard')
default_notation = 'polish'

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

def create_parser(notn=None, vocab=None, table=None, **opts):
    """
    Create a sentence parser with the given spec. This is
    useful if you parsing many sentences with the same notation
    and vocabulary.

    :param str notn: The parser notation. Uses the default notation
        if not passed.
    :param Vocabulary vocab: The vocabulary instance containing any
        custom predicate definitions. If not passed, a new instance is
        created.
    :param CharTable table: A custom parser table to use.
    :return: The parser instance
    :rtype: Parser
    """
    if isinstance(notn, Vocabulary) or isstr(vocab):
        # Accept inverted args for backwards compatibility.
        notn, vocab = (vocab, notn)
    if not vocab:
        vocab = Vocabulary()
    if not notn:
        notn = default_notation
    elif notn not in ('polish', 'standard'):
        raise ValueError('Invalid notation: {0}'.format(str(notn)))
    if not table:
        table = 'default'
    if isstr(table):
        table = CharTable.fetch(notn, table)
    if notn == 'polish':
        return PolishParser(table, vocab, **opts)
    elif notn == 'standard':
        return StandardParser(table, vocab, **opts)

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
        """
        Parse the input strings and create an argument.

        :param str conclusion: The argument's conclusion.
        :param list premises: List of premise strings, if any.
        :param str title: The title to pass to the argument's constructor.
        :return: The argument.
        :rtype: argument
        :raises ParseError:
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
    def __init__(self, table, vocab, **opts):
        self.table = table
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

        :rtype: Sentence
        :raises ParseError:
        :meta private:
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

        :rtype: AtomicSentence
        :meta private:
        """
        return Atomic(**self._read_item())

    def _read_predicate_sentence(self):
        """
        Read predicated sentence starting from the current character.

        :rtype: PredicatedSentence
        :meta private:
        """
        predicate = self._read_predicate()
        params = self._read_parameters(predicate.arity)
        return Predicated(predicate, params)

    def _read_quantified_sentence(self):
        """
        Read quantified sentence starting from the current character.

        :rtype: PredicatedSentence
        :meta private:
        """
        self._assert_current_is('quantifier')
        # quantifier = self.symbol_set.indexof('quantifier', self._current())
        _, quantifier = self.table.item(self._current())
        self._advance()
        v = self._read_variable()
        if v in list(self.bound_vars):
            # vchr = self.symbol_set.charof('variable', v.index)
            vchr = self.table.char('variable', v.index)
            raise BoundVariableError(
                "Cannot rebind variable '{0}' ({1}) at position {2}.".format(vchr, v.subscript, self.pos)
            )
        self.bound_vars.add(v)
        sentence = self._read()
        if v not in list(sentence.variables()):
            # vchr = self.symbol_set.charof('variable', v.index)
            vchr = self.table.char('variable', v.index)
            raise BoundVariableError(
                "Unused bound variable '{0}' ({1}) at position {2}.".format(vchr, v.subscript, self.pos)
            )
        self.bound_vars.remove(v)
        return Quantified(quantifier, v, sentence)

    ## ==========================================
    ##  Medium-level parsing methods - Parameters
    ## ==========================================

    def _read_predicate(self):
        """
        Read a predicate starting from the current character.

        :rtype: Predicate
        :meta private:
        """
        pchar = self._current()
        cpos = self.pos
        ctype = self._typeof(pchar)
        if ctype == 'system_predicate':
            # name = self.symbol_set.indexof(ctype, pchar)
            _, name = self.table.item(pchar)
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
        :return: A list of `Parameter` objects.
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

        :rtype: Parameter
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
                # vchr = self.symbol_set.charof('variable', v.index)
                vchr = self.table.char('variable', v.index)
                raise UnboundVariableError(
                    "Unbound variable '{0}' ({1}) at position {2}.".format(vchr, cpos, v.subscript)
                )
            return v

    def _read_variable(self):
        """
        Read a variable starting from the current character.

        :rtype: Variable
        :meta private:
        """
        return Variable(**self._read_item())

    def _read_constant(self):
        """
        Read a constant starting from the current character.

        :rtype: Constant
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
        # index = self.symbol_set.indexof(ctype, self._current())
        _, index = self.table.item(self._current())
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
        # return self.symbol_set.typeof(c)
        return self.table.type(c)

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

    # symbol_set = SymbolSet.get_instance('polish.ascii')

    def _read(self):
        ctype = self._assert_current()
        if ctype == 'operator':
            # operator = self.symbol_set.indexof('operator', self._current())
            _, operator = self.table.item(self._current())
            self._advance()
            operands = [self._read() for x in range(operarity(operator))]
            s = Operated(operator, operands)
        else:
            s = super()._read()
        return s

class StandardParser(BaseParser):

    # symbol_set = SymbolSet.get_instance('standard.ascii')

    def parse(self, string):
        # override
        try:
            s = super().parse(string)
        except ParseError as e:
            try:
                # allow dropped outer parens
                pstring = ''.join([
                    # self.symbol_set.charof('paren_open', 0),
                    self.table.char('paren_open', 0),
                    string,
                    # self.symbol_set.charof('paren_close', 0),
                    self.table.char('paren_close', 0)
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
        # operator = self.symbol_set.indexof('operator', self._current())
        _, operator = self.table.item(self._current())
        arity = operarity(operator)
        # only unary operators can be prefix operators
        if arity != 1:
            raise ParseError(
                "Unexpected non-prefix operator symbol '{0}' at position {1}.".format(
                    self._current(), self.pos
                )
            )
        self._advance()
        operand = self._read()
        return Operated(operator, [operand])

    def __read_infix_predicate_sentence(self):
        params = [self._read_parameter()]
        self._assert_current_is('user_predicate', 'system_predicate')
        ppos = self.pos
        predicate = self._read_predicate()
        if predicate.arity < 2:
            raise ParseError(
                cat("Unexpected {0}-ary predicate symbol at position {1}. ",
                "Infix notation requires arity > 1.").format(predicate.arity, ppos)
            )
        params += self._read_parameters(predicate.arity - 1)
        return Predicated(predicate, params)

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
                # peek_operator = self.symbol_set.indexof('operator', peek)
                _, peek_operator = self.table.item(peek)
                if operarity(peek_operator) == 2 and depth == 1:
                    if operator != None:
                        raise ParseError(
                            'Unexpected binary operator symbol at position {0}.'.format(self.pos + length)
                        )
                    operator_pos = self.pos + length
                    operator = peek_operator
            length += 1
        if operator == None:
            raise ParseError(
                'Parenthetical expression is missing binary operator at position {0}.'.format(self.pos)
            )
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
        return Operated(operator, [lhs, rhs])

class CharTable(object):

    __instances = {'polish': {}, 'standard': {}}

    @staticmethod
    def load(notn, name, table):
        idx = __class__.__instances[notn]
        if name in idx:
            raise ValueError('Table {0}.{1} already defined'.format(notn, name))
        idx[name] = __class__(table)
        return idx[name]

    @staticmethod
    def fetch(notn, name='default'):
        idx = __class__.__instances[notn]
        builtin = __class__.__builtin[notn]
        return idx.get(name) or __class__.load(notn, name, builtin[name])

    @staticmethod
    def available(notn):
        return sorted(set(__class__.__instances[notn]).union(__class__.__builtin[notn]))

    def __init__(self, table):
        vals, itms = table.values(), table.items()
        # copy table
        self._table = {key: tuple(value) for key, value in itms}
        # flipped table 
        self._reverse = dict(reversed(item) for item in itms)
        # list of types
        self._types = sorted(set(item[0] for item in vals))
        # tuple of unique values for type
        self._values = {
            # must be unique!
            typ: sorted(set(item[1] for item in vals if item[0] == typ))
            for typ in self._types
        }
        # chars for each type, no duplicates
        self._chars = {
            typ: tuple(self._reverse[(typ, val)] for val in self._values[typ])
            for typ in self._types
        }

    def type(self, char):
        item = self._table.get(char)
        return item[0] if item else None

    def item(self, char):
        return self._table[char]

    def value(self, char):
        return self.item(char)[1]

    def char(self, *item):
        return self._reverse[tuple(item)]

    def values(self, typ):
        return list(self._values[typ])

    def chars(self, typ):
        return list(self._chars[typ])

    def types(self):
        return list(self._types)

    def table(self):
        return dict(self._table)

    @staticmethod
    def _initbuiltin(tdata):
        __class__.__builtin = tdata
        del(__class__._initbuiltin)
    __builtin = None

CharTable._initbuiltin({
    'standard': {
        'default': {
            'A' : ('atomic', 0),
            'B' : ('atomic', 1),
            'C' : ('atomic', 2),
            'D' : ('atomic', 3),
            'E' : ('atomic', 4),
            '*' : ('operator', 'Assertion'),
            '~' : ('operator', 'Negation'),
            '&' : ('operator', 'Conjunction'),
            'V' : ('operator', 'Disjunction'),
            '>' : ('operator', 'Material Conditional'),
            '<' : ('operator', 'Material Biconditional'),
            '$' : ('operator', 'Conditional'),
            '%' : ('operator', 'Biconditional'),
            'P' : ('operator', 'Possibility'),
            'N' : ('operator', 'Necessity'),
            'x' : ('variable', 0),
            'y' : ('variable', 1),
            'z' : ('variable', 2),
            'v' : ('variable', 3),
            'a' : ('constant', 0),
            'b' : ('constant', 1),
            'c' : ('constant', 2),
            'd' : ('constant', 3),
            '=' : ('system_predicate', 'Identity'),
            '!' : ('system_predicate', 'Existence'),
            'F' : ('user_predicate', 0),
            'G' : ('user_predicate', 1),
            'H' : ('user_predicate', 2),
            'O' : ('user_predicate', 3),
            'L' : ('quantifier', 'Universal'),
            'X' : ('quantifier', 'Existential'),
            '(' : ('paren_open', 0),
            ')' : ('paren_close', 0),
            ' ' : ('whitespace', 0),
            '0' : ('digit', 0),
            '1' : ('digit', 1),
            '2' : ('digit', 2),
            '3' : ('digit', 3),
            '4' : ('digit', 4),
            '5' : ('digit', 5),
            '6' : ('digit', 6),
            '7' : ('digit', 7),
            '8' : ('digit', 8),
            '9' : ('digit', 9),
        }
    },
    'polish': {
        'default': {
            'a' : ('atomic', 0),
            'b' : ('atomic', 1),
            'c' : ('atomic', 2),
            'd' : ('atomic', 3),
            'e' : ('atomic', 4),
            'T' : ('operator', 'Assertion'),
            'N' : ('operator', 'Negation'),
            'K' : ('operator', 'Conjunction'),
            'A' : ('operator', 'Disjunction'),
            'C' : ('operator', 'Material Conditional'),
            'E' : ('operator', 'Material Biconditional'),
            'U' : ('operator', 'Conditional'),
            'B' : ('operator', 'Biconditional'),
            'M' : ('operator', 'Possibility'),
            'L' : ('operator', 'Necessity'),
            'x' : ('variable', 0),
            'y' : ('variable', 1),
            'z' : ('variable', 2),
            'v' : ('variable', 3),
            'm' : ('constant', 0),
            'n' : ('constant', 1),
            'o' : ('constant', 2),
            's' : ('constant', 3),
            'I' : ('system_predicate', 'Identity'),
            'J' : ('system_predicate', 'Existence'),
            'F' : ('user_predicate', 0),
            'G' : ('user_predicate', 1),
            'H' : ('user_predicate', 2),
            'O' : ('user_predicate', 3),
            'V' : ('quantifier', 'Universal'),
            'S' : ('quantifier', 'Existential'),
            ' ' : ('whitespace', 0),
            '0' : ('digit', 0),
            '1' : ('digit', 1),
            '2' : ('digit', 2),
            '3' : ('digit', 3),
            '4' : ('digit', 4),
            '5' : ('digit', 5),
            '6' : ('digit', 6),
            '7' : ('digit', 7),
            '8' : ('digit', 8),
            '9' : ('digit', 9),
        },
    }
})