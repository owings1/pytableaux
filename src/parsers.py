# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
# pytableaux - parsers module
from __future__ import annotations

__all__ = (
    'CharTable',
    'BaseParser',
    'PolishParser',
    'StandardParser',
)

from errors import (
    Emsg,
    ParseError,
    BoundVariableError,
    UnboundVariableError,
    IllegalStateError,
)
from tools.callables import gets
from tools.decorators import abstract, raisr
from tools.hybrids import qset
from tools.mappings import ItemsIterator, MapCover, MapProxy, dmap
from tools.sequences import seqf
from tools.sets import setf, EMPTY_SET

from lexicals import (
    Bases as _Bases,
    Lexical,
    BiCoords,
    Operator as Oper, Quantifier,
    Predicate, Parameter, Constant, Variable,
    Sentence, Atomic, Predicated, Quantified, Operated,
    LexType, Predicates, Argument, Marking, Notation, Parser,
)

from collections.abc import Set
from typing import (
    # Any,
    # Iterable,
    Mapping,
)

notations = Notation.seq

CType = LexType|Marking|type[Predicate.System]

class CharTable(MapCover[str, tuple[CType, int|Lexical]], _Bases.CacheNotationData):

    default_fetch_name = 'default'

    __slots__ = 'reversed', 'chars'

    reversed: Mapping[tuple[CType, int|Lexical], str]
    chars: Mapping[CType, seqf[str]]

    def __init__(self, data: Mapping[str, tuple[CType, int|Lexical]]):

        super().__init__(MapProxy(data))

        vals = self.values()

        # list of types
        ctypes: qset[CType] = qset(map(gets.Key0, vals))

        tvals: dmap[CType, qset[int|Lexical]] = dmap()
        for ctype in ctypes:
            tvals[ctype] = qset()
        for ctype, value in vals:
            tvals[ctype].add(value)
        for ctype in ctypes:
            tvals[ctype].sort()

        # flipped table
        self.reversed = MapCover(dmap(
            map(reversed, ItemsIterator(self))
        ))

        # chars for each type in value order, duplicates discarded
        self.chars = MapCover(dmap(
            (ctype, seqf(self.reversed[ctype, val] for val in tvals[ctype]))
            for ctype in ctypes
        ))

    def type(self, char):
        """
        :param str char: The character symbol.
        :return: The symbol type, or ``None`` if not in table.
        :raises TypeError: for unhashable type, e.g. dict.
        """
        return self[char][0]

    def value(self, char):
        """
        :param str char: The character symbol.
        :return: Table item value, e.g. ``1`` or ``Operator.Negation``.
        :raises KeyError: if symbol not in table.
        """
        return self[char][1]

    def char(self, *item):
        return self.reversed[item]

    def __setattr__(self, name, value):
        if name in self.__slots__ and hasattr(self, name):
            raise AttributeError(name)
        super().__setattr__(name, value)

    __delattr__ = raisr(AttributeError)

def parse(input: str, *args, **opts) -> Sentence:
    """
    Parse a string and return a sentence.
    Convenience wrapper for ``create_parser().parse()``.
    """
    return create_parser(*args, **opts).parse(input)

def parse_argument(conclusion, premises = None, title: str = None, **opts) -> Argument:
    """
    Parse conclusion, and optional premises, and return an argument.
    Convenience wrapper for ``create_parser().parse_argument()``.

    :rtype: lexicals.Argument
    """
    return create_parser(**opts).argument(conclusion, premises, title = title)

def create_parser(notn: Notation = None, vocab: Predicates = None, table: CharTable = None, **opts) -> BaseParser:
    """
    Create a sentence parser with the given spec. This is
    useful if you parsing many sentences with the same notation
    and vocabulary.

    :param notn: The parser notation. Uses the default notation if not passed.
    :param vocab: The predicates store for parsing user-defined predicates.
    :param CharTable table: A custom parser table to use.
    :return: The parser instance
    :raises ValueError: on invalid notation, or table.
    :raises TypeError: on invalid argument types.
    """
    if isinstance(notn, Predicates) or isinstance(vocab, (Notation, str)):
        # Accept inverted args for backwards compatibility.
        notn, vocab = (vocab, notn)
    if vocab is None:
        vocab = Predicates.System
    if notn is None:
        notn = Notation.default
    else:
        notn = Notation(notn)
    if table is None:
        table = CharTable.default_fetch_name
    if isinstance(table, str):
        table = CharTable.fetch(notn, table)
    return notn.Parser(table, vocab, **opts)

class ParseContext:

    __slots__ = 'input', 'type', 'preds', 'is_open', 'pos', 'bound_vars'

    def __init__(self, input_: str, table: CharTable, preds: Predicates, /):
        self.input = input_
        self.type = table.type
        self.preds = preds
        self.is_open = False

    def __enter__(self):
        if self.is_open:
            raise IllegalStateError('Context already open')
        self.is_open = True
        self.bound_vars = set()
        self.pos = 0
        return self

    def __exit__(self, typ, value, traceback):
        self.is_open = False
        del(self.pos, self.bound_vars)

    def current(self):
        'Return the current character, or ``None`` if after last.'
        try:
            return self.input[self.pos]
        except IndexError:
            return None

    def next(self, n: int = 1):
        'Get the nth character after the current, or ``None``.'
        try:
            return self.input[self.pos + n]
        except IndexError:
            return None

    def assert_current(self):
        """
        :return: Type of current char, e.g. ``'operator'``, or ``None`` if
          uknown type.
        :raises errors.ParseError: if after last.
        """
        if not self.has_current():
            raise ParseError(
                'Unexpected end of input at position %d.' % self.pos
            )
        return self.type(self.current())

    def assert_current_is(self, ctype: str):
        """
        :param str ctype:
        :raises errors.ParseError: if after last, unexpected type or unknown symbol.
        """
        if self.assert_current() != ctype:
            raise ParseError(self._unexp_msg(ctype))

    def assert_current_in(self, ctypes: Set):
        ctype = self.assert_current()
        if ctype in ctypes:
            return ctype
        raise ParseError(self._unexp_msg(*ctypes))

    def assert_end(self):
        'Raise an error if not after last.'
        if len(self.input) > self.pos:
            raise ParseError(self._unexp_msg())

    def has_next(self, n: int = 1):
        'Whether there are n-many characters after the current.'
        return len(self.input) > self.pos + n

    def has_current(self):
        'Whether there is a current character.'
        return len(self.input) > self.pos

    def advance(self, n: int = 1):
        'Advance the current pointer n-many characters, and then eat whitespace.'
        self.pos += n  
        self.chomp()
        return self

    def chomp(self):
        'Proceeed through whitepsace.'
        try:
            while self.type(self.input[self.pos]) is Marking.whitespace:
                self.pos += 1
        except IndexError:
            pass
        return self

    def _unexp_msg(self, *exp):
        char = self.input[self.pos]
        ctype = self.type(char)
        if ctype is None:
            pfx = 'Unexpected symbol'
        else:
            pfx = 'Unexpected %s symbol' % ctype
        msg = "%s '%s' at position %d." % (pfx, char, self.pos)
        if len(exp):
            msg += ' Expected %s.' % ', '.join(map(str, exp))
        return msg


_PRED_CTYPES = setf({LexType.Predicate, Predicate.System})
_BASE_CTYPES = _PRED_CTYPES | {LexType.Quantifier, LexType.Atomic}
_PARAM_CTYPES = setf({LexType.Constant, LexType.Variable})

class BaseParser(Parser):

    __slots__ = 'table', 'preds', 'opts'

    def __init__(self, table: CharTable, preds: Predicates = Predicate.System, /, **opts):
        self.table = table
        self.preds = preds
        self.opts = opts

    def parse(self, input_: str, /):
        if isinstance(input_, Sentence):
            return input_
        with ParseContext(input_, self.table, self.preds) as context:
            context.chomp()
            s = self._read(context)
            context.chomp()
            context.assert_end()
            return s

    @abstract
    def _read(self, context: ParseContext) -> Sentence:
        """
        Internal entrypoint for reading a sentence. Implementation is recursive.
        This provides the default implementation for prefix notation sentences,
        i.e. atomic, predicated, and quantified sentences.

        This does not parse operated sentences, Subclasses *must* override
        this method, and delegate to ``super()`` for the default implementation
        when appropriate.

        :rtype: lexicals.Sentence
        :raises errors.ParseError:
        :meta private:
        """
        ctype = context.assert_current_in(_BASE_CTYPES)
        if ctype is LexType.Atomic:
            return self._read_atomic(context)
        if ctype is LexType.Quantifier:
            return self._read_quantified(context)
        return self._read_predicated(context)

    def _read_atomic(self, context: ParseContext):
        'Read an atomic sentence.'
        return Atomic(self._read_coords(context))

    def _read_predicated(self, context: ParseContext):
        'Read a predicated sentence.'
        pred = self._read_predicate(context)
        return Predicated(pred, self._read_params(context, pred.arity))

    def _read_quantified(self, context: ParseContext):
        'Read a quantified sentence.'
        q = self.table.value(context.current())
        context.advance()
        v = self._read_variable(context)
        if v in context.bound_vars:
            vchr = self.table.char(LexType.Variable, v.index)
            raise BoundVariableError(
                "Cannot rebind variable '{0}' ({1}) at position {2}.".format(
                    vchr, v.subscript, context.pos
                )
            )
        context.bound_vars.add(v)
        s = self._read(context)
        if v not in s.variables:
            vchr = self.table.reversed[LexType.Variable, v.index]
            raise BoundVariableError(
                "Unused bound variable '{0}' ({1}) at position {2}.".format(
                    vchr, v.subscript, context.pos
                )
            )
        context.bound_vars.remove(v)
        return Quantified(q, v, s)

    def _read_predicate(self, context: ParseContext):
        'Read a predicate.'
        pchar = context.current()
        cpos = context.pos
        ctype = self.table.type(pchar)
        if ctype is Predicate.System:
            pred: Predicate = self.table.value(pchar)
            context.advance()
            return pred
        try:
            return self.preds.get(self._read_coords(context))
        except KeyError:
            raise ParseError(
                "Undefined predicate symbol '{0}' at position {1}.".format(pchar, cpos)
            )

    def _read_params(self, context: ParseContext, num: int):
        'Read the given number of parameters.'
        return tuple(self._read_parameter(context) for _ in range(num))

    def _read_parameter(self, context: ParseContext) -> Parameter:
        'Read a single parameter (constant or variable)'
        ctype = context.assert_current_in(_PARAM_CTYPES)
        if ctype is LexType.Constant:
            return self._read_constant(context)
        cpos = context.pos
        v = self._read_variable(context)
        if v not in context.bound_vars:
            vchr = self.table.reversed[LexType.Variable, v.index]
            raise UnboundVariableError(
                "Unbound variable '%s_%d' at position %d." % (
                    vchr, v.subscript, cpos
                )
            )
        return v

    def _read_variable(self, context: ParseContext):
        'Read a variable.'
        return Variable(self._read_coords(context))

    def _read_constant(self, context: ParseContext):
        'Read a constant.'
        return Constant(self._read_coords(context))

    def _read_subscript(self, context: ParseContext):
        """Read the subscript starting from the current character. If the current
        character is not a digit, or we are after last, then the subscript is
        ``0```. Otherwise, all consecutive digit characters are read
        (whitespace allowed), and then converted to an integer, which is then
        returned."""
        # TODO: use better list, e.g. linked.
        digits = []
        while context.current() and self.table.type(context.current()) == Marking.digit:
            digits.append(context.current())
            context.advance()
        if not len(digits):
            return 0
        return int(''.join(digits))

    def _read_coords(self, context: ParseContext):
        """Read (index, subscript) coords starting from the current character,
        which must be in the list of characters given. `index` is the list index in
        the symbol set. This is a generic way to read user predicates,
        atomics, variables, constants, etc. Note, this will not work for
        system predicates, because they have string keys in the symbols set."""
        index = self.table.value(context.current())
        context.advance()
        return BiCoords(index, self._read_subscript(context))

    def __setattr__(self, name, value):
        if name in self.__slots__ and hasattr(self, name):
            raise AttributeError(name)
        super().__setattr__(name, value)

    __delattr__ = raisr(AttributeError)

class PolishParser(BaseParser):

    __slots__ = EMPTY_SET

    def _read(self, context: ParseContext):
        ctype = context.assert_current()
        if ctype is LexType.Operator:
            oper: Oper = self.table.value(context.current())
            context.advance()
            s = Operated(
                oper,
                tuple(self._read(context) for _ in range(oper.arity))
            )
        else:
            s = super()._read(context)
        return s

Notation.polish.Parser = PolishParser

class StandardParser(BaseParser):

    __slots__ = EMPTY_SET

    def parse(self, input):
        pass
        # Override to allow dropped outer parens.
        try:
            return super().parse(input)
        except ParseError:
            try:
                return super().parse(''.join((
                    self.table.reversed[Marking.paren_open, 0],
                    input,
                    self.table.reversed[Marking.paren_close, 0]
                )))
            except ParseError:
                pass
            raise

    def _read(self, context: ParseContext):
        ctype = context.assert_current()
        if ctype is LexType.Operator:
            return self.__read_operated(context)
        if ctype is Marking.paren_open:
            return self.__read_from_paren_open(context)
        if ctype is LexType.Constant:
            return self.__read_infix_predicated(context)
        return super()._read(context)

    def __read_operated(self, context: ParseContext):
        oper: Oper = self.table.value(context.current())
        # only unary operators can be prefix operators
        if oper.arity != 1:
            raise ParseError(
                "Unexpected non-prefix operator symbol '{0}' at position {1}.".format(
                    context.current(), context.pos
                )
            )
        context.advance()
        return Operated(oper, (self._read(context),))

    def __read_infix_predicated(self, context: ParseContext):
        lhp = self._read_parameter(context)
        context.assert_current_in(_PRED_CTYPES)
        ppos = context.pos
        pred = self._read_predicate(context)
        arity = pred.arity
        if arity < 2:
            raise ParseError(
                "Unexpected {0}-ary predicate symbol at position {1}. "
                "Infix notation requires arity > 1.".format(arity, ppos)
            )
        return Predicated(pred, (lhp, *self._read_params(context, arity - 1)))

    def __read_from_paren_open(self, context: ParseContext):
        # if we have an open parenthesis, then we demand a binary infix operator sentence.
        # scan ahead to:
        #   - find the corresponding close parenthesis position
        #   - find the binary operator and its position
        oper = oper_pos = None
        depth = length = 1
        while depth:
            if not context.has_next(length):
                raise ParseError(
                    'Unterminated open paren at position %d.' % context.pos
                )
            peek = context.next(length)
            ptype = self.table.type(peek)
            if ptype is Marking.paren_close:
                depth -= 1
            elif ptype is Marking.paren_open:
                depth += 1
            elif ptype is LexType.Operator:
                peek_oper: Oper = self.table.value(peek)
                if peek_oper.arity == 2 and depth == 1:
                    if oper is not None:
                        msg = 'Unexpected binary operator symbol at position %d.' % (
                            context.pos + length
                        ) 
                        raise ParseError(msg)
                    oper_pos = context.pos + length
                    oper = peek_oper
            length += 1
        if oper is None:
            raise ParseError(
                'Paren expression missing binary operator at position {0}.'.format(context.pos)
            )
        # now we can divide the string into lhs and rhs
        lhs_start = context.pos + 1
        # move past the open paren
        context.advance()
        # read the lhs
        lhs = self._read(context)
        context.chomp()
        if context.pos != oper_pos:
            raise ParseError(
                'Invalid left side expression starting at position {0} '
                'and ending at position {1}, which proceeds past operator '
                '({2}) at position {3}.'.format(
                    lhs_start, context.pos, oper, oper_pos
                )
            )
        # move past the operator
        context.advance()
        # read the rhs
        rhs = self._read(context)
        context.chomp()
        # now we should have a close paren
        context.assert_current_is(Marking.paren_close)
        # move past the close paren
        context.advance()
        return Operated(oper, (lhs, rhs))

Notation.standard.Parser = StandardParser

CharTable._initcache(Notation, {
    Notation.standard: {
        'default': {
            'A' : (LexType.Atomic, 0),
            'B' : (LexType.Atomic, 1),
            'C' : (LexType.Atomic, 2),
            'D' : (LexType.Atomic, 3),
            'E' : (LexType.Atomic, 4),
            '*' : (LexType.Operator, Oper.Assertion),
            '~' : (LexType.Operator, Oper.Negation),
            '&' : (LexType.Operator, Oper.Conjunction),
            'V' : (LexType.Operator, Oper.Disjunction),
            '>' : (LexType.Operator, Oper.MaterialConditional),
            '<' : (LexType.Operator, Oper.MaterialBiconditional),
            '$' : (LexType.Operator, Oper.Conditional),
            '%' : (LexType.Operator, Oper.Biconditional),
            'P' : (LexType.Operator, Oper.Possibility),
            'N' : (LexType.Operator, Oper.Necessity),
            'x' : (LexType.Variable, 0),
            'y' : (LexType.Variable, 1),
            'z' : (LexType.Variable, 2),
            'v' : (LexType.Variable, 3),
            'a' : (LexType.Constant, 0),
            'b' : (LexType.Constant, 1),
            'c' : (LexType.Constant, 2),
            'd' : (LexType.Constant, 3),
            '=' : (Predicate.System, Predicate.System.Identity),
            '!' : (Predicate.System, Predicate.System.Existence),
            'F' : (LexType.Predicate, 0),
            'G' : (LexType.Predicate, 1),
            'H' : (LexType.Predicate, 2),
            'O' : (LexType.Predicate, 3),
            'L' : (LexType.Quantifier, Quantifier.Universal),
            'X' : (LexType.Quantifier, Quantifier.Existential),
            '(' : (Marking.paren_open, 0),
            ')' : (Marking.paren_close, 0),
            ' ' : (Marking.whitespace, 0),
            '0' : (Marking.digit, 0),
            '1' : (Marking.digit, 1),
            '2' : (Marking.digit, 2),
            '3' : (Marking.digit, 3),
            '4' : (Marking.digit, 4),
            '5' : (Marking.digit, 5),
            '6' : (Marking.digit, 6),
            '7' : (Marking.digit, 7),
            '8' : (Marking.digit, 8),
            '9' : (Marking.digit, 9),
        }
    },
    Notation.polish: {
        'default': {
            'a' : (LexType.Atomic, 0),
            'b' : (LexType.Atomic, 1),
            'c' : (LexType.Atomic, 2),
            'd' : (LexType.Atomic, 3),
            'e' : (LexType.Atomic, 4),
            'T' : (LexType.Operator, Oper.Assertion),
            'N' : (LexType.Operator, Oper.Negation),
            'K' : (LexType.Operator, Oper.Conjunction),
            'A' : (LexType.Operator, Oper.Disjunction),
            'C' : (LexType.Operator, Oper.MaterialConditional),
            'E' : (LexType.Operator, Oper.MaterialBiconditional),
            'U' : (LexType.Operator, Oper.Conditional),
            'B' : (LexType.Operator, Oper.Biconditional),
            'M' : (LexType.Operator, Oper.Possibility),
            'L' : (LexType.Operator, Oper.Necessity),
            'x' : (LexType.Variable, 0),
            'y' : (LexType.Variable, 1),
            'z' : (LexType.Variable, 2),
            'v' : (LexType.Variable, 3),
            'm' : (LexType.Constant, 0),
            'n' : (LexType.Constant, 1),
            'o' : (LexType.Constant, 2),
            's' : (LexType.Constant, 3),
            'I' : (Predicate.System, Predicate.System.Identity),
            'J' : (Predicate.System, Predicate.System.Existence),
            'F' : (LexType.Predicate, 0),
            'G' : (LexType.Predicate, 1),
            'H' : (LexType.Predicate, 2),
            'O' : (LexType.Predicate, 3),
            'V' : (LexType.Quantifier, Quantifier.Universal),
            'S' : (LexType.Quantifier, Quantifier.Existential),
            ' ' : (Marking.whitespace, 0),
            '0' : (Marking.digit, 0),
            '1' : (Marking.digit, 1),
            '2' : (Marking.digit, 2),
            '3' : (Marking.digit, 3),
            '4' : (Marking.digit, 4),
            '5' : (Marking.digit, 5),
            '6' : (Marking.digit, 6),
            '7' : (Marking.digit, 7),
            '8' : (Marking.digit, 8),
            '9' : (Marking.digit, 9),
        },
    }
})
