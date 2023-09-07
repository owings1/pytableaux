# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
"""
pytableaux.lang.parsing
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from abc import abstractmethod as abstract
from collections import deque
from enum import Enum
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Any, ClassVar, Iterable, Iterator, Mapping,
                    Self, TypeVar)

from ..errors import (BoundVariableError, Emsg, IllegalStateError, ParseError,
                      UnboundVariableError, UndefinedPredicateError, check)
from ..tools import MapCover, abcs, for_defaults
from . import BiCoords, LangCommonMeta, Marking, Notation
from .collect import Argument, Predicates, PredicatesBase
from .lex import (Atomic, Constant, Operated, Operator, Parameter, Predicate,
                  Predicated, Quantified, Quantifier, Sentence, Variable)

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'Parser',
    'ParseContext',
    'ParseTable',
    'PolishParser',
    'StandardParser')

_T = TypeVar('_T')
NOARG = object()


class ParserMeta(LangCommonMeta):
    'Parser Metaclass.'

    DEFAULT_NOTATION: Notation = Notation.polish

    if TYPE_CHECKING:
        @overload
        def __call__(cls,
            notation:Notation|None=None,
            predicates:Predicates|None=None,
            table:ParseTable|str|None = None,
            **opts) -> Parser:...
        
    def __call__(cls, *args, **kw) -> Parser:
        if cls is Parser:
            if args:
                notn = Notation(args[0])
                args = args[1:]
            else:
                notn = Notation(kw.pop('notation', Parser.DEFAULT_NOTATION))
            return notn.Parser(*args, **kw)
        return super().__call__(*args, **kw)

class Parser(metaclass=ParserMeta):
    """Parser interface and coordinator.

    To create a parser::

        >>> from pytableaux.lang import Parser
        >>> Parser()
        <PolishParser:(<Notation.polish>, 'default')>
        >>> Parser('standard')
        <StandardParser:(<Notation.standard>, 'default')>
    
    Or use the :class:`Notation` enum class::

        >>> from pytableaux.lang import Notation
        >>> Parser(Notation.standard)
        <StandardParser:(<Notation.standard>, 'default')>
        >>> Notation.polish.Parser()
        <PolishParser:(<Notation.polish>, 'default')>

    To parse :class:`Predicated` sentences, the parser must know the predicate's
    `arity`. By default, it will deduce the arity from the first usage.

        >>> parser = Parser(notation='standard')
        >>> parser('Fa & Gab')
        <Sentence: Fa ∧ Gab>
        >>> parser.predicates
        Predicates({<Predicate: F>, <Predicate: G>})
        >>> # parser('Fab') # raises ParseError

    Alternatively, pass a :class:`Predicates` object with the predicates::

        >>> from pytableaux.lang import Predicates
        >>> preds = Predicates(((0, 0, 1), (1, 0, 2)))
        >>> parser = Parser('standard', preds, auto_preds=False)
        >>> parser('Fa & Gab')
        <Sentence: Fa ∧ Gab>
    """

    __slots__ = ('table', 'predicates', 'opts')

    notation: ClassVar[Notation]
    "The parser notation."

    defaults: ClassVar[dict] = dict(auto_preds=True)
    "The default options."

    table: ParseTable
    "The parse table instance."

    predicates: Predicates
    "The predicates store."

    opts: Mapping
    "The parser options."

    if TYPE_CHECKING:
        @overload
        def __init__(self,
            notation:Notation|None=None,
            predicates:Predicates|None=None,
            table:ParseTable|str|None = None,
            **opts): ...
        
    def __init__(self, predicates:Predicates|None=None, table:ParseTable|str|None = None, **opts):
        """
        Options:
            auto_preds: Deduce predicate arity from first usage. Default ``True``.
        """
        if table is None:
            self.table = ParseTable.fetch(self.notation)
        elif isinstance(table, str):
            self.table = ParseTable.fetch(self.notation, table)
        else:
            self.table = check.inst(table, ParseTable)
        if predicates is None:
            predicates = Predicates()
        else:
            if not isinstance(predicates, PredicatesBase):
                predicates = Predicates(predicates)
        self.predicates = predicates
        self.opts = for_defaults(self.defaults, opts)

    @abstract
    def __call__(self, input: str, /) -> Sentence:
        """Parse a sentence from an input string.

        Args:
            input: The input string.
        
        Returns:
            Sentence: The parsed sentence.

        Raises:
            ParseError
        """
        raise NotImplementedError

    def argument(self, conclusion: str, premises: Iterable[str] = None, *, title: str|None = None) -> Argument:
        """Parse the input strings and create an argument.

        Args:
            conclusion: The argument's conclusion.
            premises: Premise strings, if any.
        
        Keyword Args:
            title: An optional title.

        Returns:
            The argument.

        Raises:
            ParseError: if input cannot be parsed.
            TypeError: for bad argument types.
        """
        return Argument(
            self(conclusion),
            premises and map(self, premises),
            title=title)

    def __repr__(self):
        return f'<{type(self).__name__}:{self.table.notation}.{self.table.dialect}>'

    def __init_subclass__(cls, primary = False, **kw):
        'Merge ``_defaults``, set primary.'
        super().__init_subclass__(**kw)
        abcs.merge_attr(cls, 'defaults', supcls=__class__)
        if primary:
            cls.notation.Parser = cls

class ParseContext:
    "Parse context."

    __slots__ = (
        'bound',
        'input',
        'is_open',
        'pos',
        'predicates',
        'table')

    bound: set[Variable]
    input: str
    is_open: bool
    pos: int
    predicates: PredicatesBase
    table: ParseTable

    def __init__(self, input: str, table: ParseTable, predicates: PredicatesBase, /):
        self.input = input
        self.table = table
        self.predicates = predicates
        self.is_open = False

    def open(self) -> Self:
        """Open the context. A context can only be opened once.
        """
        if self.is_open:
            raise IllegalStateError('Context already open')
        self.is_open = True
        self.bound = set()
        self.pos = 0
        self.chomp()
        return self

    def close(self):
        """Close the context. Eats remaining whitespace and checks that the
        input is fully consumed.

        Raises:
            ParseError: if input is not fully consumed.
        """
        self.chomp()
        self.assert_end()

    def __enter__(self) -> Self:
        return self.open()

    def __exit__(self, typ, value, traceback):
        self.close()

    def current(self) -> str|None:
        'Return the current character, or ``None`` if after last.'
        try:
            return self.input[self.pos]
        except IndexError:
            pass

    def next(self, n: int = 1, /) -> str|None:
        'Get the nth character after the current, or ``None``.'
        try:
            return self.input[self.pos + n]
        except IndexError:
            pass

    def assert_current(self) -> Any:
        """
        Returns:
            Type of current char, e.g. ``Operator``, or ``None`` if
            unknown type.

        Raises:
            ParseError: if after last.
        """
        if not self.has_current():
            raise ParseError(f'Unexpected end of input at position {self.pos}.')
        return self.type(self.current(), None)

    def assert_current_is(self, ctype: Any, /):
        """
        Args:
            ctype (Any): Char type

        Raises
            ParseError: if after last, unexpected type or unknown symbol.
        """
        if self.assert_current() is not ctype:
            raise ParseError(self._unexp_msg())

    def assert_current_in(self, ctypes: Iterable[_T], /) -> _T:
        ctype = self.assert_current()
        if ctype in ctypes:
            return ctype
        raise ParseError(self._unexp_msg())

    def assert_end(self):
        'Raise an error if not after last.'
        if len(self.input) > self.pos:
            raise ParseError(self._unexp_msg())

    def has_next(self, n = 1, /) -> bool:
        'Whether there are n-many characters after the current.'
        return len(self.input) > self.pos + n

    def has_current(self) -> bool:
        'Whether there is a current character.'
        return len(self.input) > self.pos

    def advance(self, n: int = 1, /) -> Self:
        """Advance the current pointer n-many characters, and then eat whitespace.

        Args:
            n: The number of characters to advance, default ``1``.

        Returns:
            self
        """
        self.pos += n  
        self.chomp()
        return self

    def chomp(self) -> ParseContext:
        """Proceeed through whitepsace.
        
        Returns:
            self
        """
        try:
            while self.type(self.input[self.pos], None) is Marking.whitespace:
                self.pos += 1
        except IndexError:
            pass
        return self

    def type(self, char: str, default = NOARG, /) -> Any:
        """Get the item type for the character.

        Args:
            char: The character symbol.
            default: The value to return if missing.

        Returns:
            The symbol type, or ``default`` if provided.

        Raises:
            KeyError: if symbol not in table and no default passed.
        """
        try:
            return self.table[char][0]
        except KeyError:
            if default is NOARG:
                raise
            return default

    def value(self, char: str, /) -> Any:
        """Get the item value for the character.

        Args:
            char: The character symbol.

        Returns:
            Table item value, e.g. ``1`` or ``Operator.Negation``.

        Raises:
            KeyError: if symbol not in table.
        """
        return self.table[char][1]

    def bind(self, v: Variable, /) -> Variable:
        """Add a variable to the set of bound variables, checking that it is
        not already bound.

        Args:
            v (Variable): The variable.
        
        Returns:
            Variable: The variable passed.
        
        Raises:
            BoundVariableError: if variable already bound.
        """
        if v in self.bound:
            raise BoundVariableError(
                f"Cannot rebind variable {v.spec} near position {self.pos}.")
        self.bound.add(v)
        return v

    def check_bound(self, v: Variable, /) -> Variable:
        """Check that a variable is already bound.

        Args:
            v (Variable): The variable.
        
        Returns:
            Variable: The variable passed.
        
        Raises:
            UnboundVariableError: if variable is not bound.
        """
        if v not in self.bound:
            raise UnboundVariableError(
                f"Unbound variable {v.spec} near position {self.pos}")
        return v

    def unbind(self, v: Variable, s: Sentence, /) -> tuple[Variable, Sentence]:
        """Unbind a variable, checking that it is already bound, and used
        within the sentence.

        Args:
            v (Variable): The variable.
            s (Sentence): The sentence using the variable.
        
        Returns:
            tuple[Variable, Sentence]: The variable and sentence passed.

        Raises:
            UnboundVariableError: if variable is not bound.
            BoundVariableError: if variable is not used in the sentence.
        """
        if self.check_bound(v) not in s.variables:
            raise BoundVariableError(
                f"Unused bound variable {v.spec} near position {self.pos}")
        self.bound.remove(v)
        return v, s

    def _unexp_msg(self) -> str:
        char = self.input[self.pos]
        ctype = self.type(char, None)
        if ctype is None:
            pfx = 'Unexpected symbol'
        else:
            pfx = f'Unexpected {ctype} symbol'
        return f"{pfx} '{char}' at position {self.pos}"

class Ctype(frozenset, Enum):
    pred = {Predicate, Predicate.System}
    param = {Constant, Variable}

class DefaultParser(Parser):
    """Parser default implementation.
    """

    def __call__(self, input: str, /) -> Sentence:
        if isinstance(input, Sentence):
            return input
        with ParseContext(input, self.table, self.predicates) as context:
            return self._read(context)

    _methodmap = MapProxy({
        Operator: '_read_operated',
        Atomic: '_read_atomic',
        Quantifier: '_read_quantified',
        Predicate: '_read_predicated',
        Predicate.System: '_read_predicated'})

    def _read(self, context: ParseContext, /) -> Sentence:
        """
        Internal entrypoint for reading a sentence. Implementation is recursive.
        This provides the default implementation for prefix notation sentences,
        i.e. atomic, predicated, and quantified sentences.

        Args:
            context (ParseContext): The parse context

        Returns:
            Sentence: The sentence

        Raises:
            ParseError:
        """
        try:
            method = self._methodmap[context.assert_current()]
        except KeyError:
            raise ParseError(context._unexp_msg()) from None
        return getattr(self, method)(context)

    @abstract
    def _read_operated(self, context: ParseContext, /) -> Operated:
        raise NotImplementedError

    def _read_atomic(self, context: ParseContext, /) -> Atomic:
        'Read an atomic sentence.'
        return Atomic(self._read_coords(context))

    def _read_predicated(self, context: ParseContext, /) -> Predicated:
        'Read a predicated sentence.'
        try:
            pred = self._read_predicate(context)
        except UndefinedPredicateError as err:
            if not self.opts['auto_preds']:
                raise
            coords = err.coords
        else:
            return pred(self._read_params(context, pred.arity))
        params = tuple(self._read_params_auto(context))
        arity = len(params)
        try:
            pred = Predicate(*coords, arity)
        except ValueError as err:
            raise ParseError(
                f'Error auto-creating predicate {coords=} {arity=}: {err}')
        self.predicates.add(pred)
        return pred(params)

    def _read_quantified(self, context: ParseContext, /) -> Quantified:
        'Read a quantified sentence.'
        quant = context.value(context.current())
        context.advance()
        context.assert_current_is(Variable)
        return quant(
            *context.unbind(
                context.bind(Variable(self._read_coords(context))),
                self._read(context)))

    def _read_predicate(self, context: ParseContext, /) -> Predicate:
        'Read a predicate.'
        pchar = context.current()
        if context.type(pchar) is Predicate.System:
            context.advance()
            return Predicate(context.value(pchar))
        coords = self._read_coords(context)
        try:
            return self.predicates.get(coords)
        except KeyError:
            raise UndefinedPredicateError(
                coords,
                f"Undefined predicate symbol '{pchar}' at position {context.pos}")

    def _read_params(self, context: ParseContext, num: int, /) -> Iterator[Parameter]:
        'Read the given number of parameters.'
        read = self._read_parameter
        for _ in range(num):
            yield read(context)

    def _read_params_auto(self, context: ParseContext, /) -> Iterator[Parameter]:
        'Read indefinite number of parameters'
        read = self._read_parameter
        ftype = context.type
        fcurr = context.current
        ctypes = Ctype.param
        while ftype(fcurr(), None) in ctypes:
            yield read(context)

    def _read_parameter(self, context: ParseContext, /) -> Parameter:
        'Read a single parameter (constant or variable)'
        ctype = context.assert_current_in(Ctype.param)
        param = ctype(self._read_coords(context))
        if ctype is Variable:
            context.check_bound(param)
        return param

    def _read_subscript(self, context: ParseContext, /) -> int:
        """Read the subscript starting from the current character. If the current
        character is not a digit, or we are after last, then the subscript is
        ``0```. Otherwise, all consecutive digit characters are read
        (whitespace allowed), and then converted to an integer, which is then
        returned.
        """
        digits = deque()
        while True:
            cur = context.current()
            if context.type(cur, None) is not Marking.digit:
                break
            digits.append(context.value(cur))
            context.advance()
        return int(''.join(map(str, digits)) or 0)

    def _read_coords(self, context: ParseContext, /) -> BiCoords:
        """Read (index, subscript) coords starting from the current character,
        which must be in the list of characters given. `index` is the list index in
        the symbol set. This is a generic way to read user predicates,
        atomics, variables, constants, etc. Note, this will not work for
        system predicates, because they have string keys in the symbols set.
        """
        index = context.value(context.current())
        context.advance()
        return BiCoords(index, self._read_subscript(context))

    __delattr__ = Emsg.ReadOnly.razr

class PolishParser(DefaultParser, primary=True):
    "Polish notation parser."

    notation = Notation.polish

    def _read_operated(self, context: ParseContext, /) -> Operated:
        oper = Operator(context.value(context.current()))
        context.advance()
        return oper(self._read(context) for _ in range(oper.arity))

class StandardParser(DefaultParser, primary=True):
    """Standard notation parser.

    Options:
        drop_parens: Don't require parentheses on all binary sentences. Default ``True``.
    """

    notation = Notation.standard
    defaults = dict(drop_parens=True)

    def __call__(self, input: str, /) -> Sentence:
        try:
            return super().__call__(input)
        except ParseError:
            if self.opts['drop_parens']:
                rev = self.table.reversed
                popen = rev[Marking.paren_open]
                pclose = rev[Marking.paren_close]
                try:
                    return super().__call__(f'{popen}{input}{pclose}')
                except ParseError:
                    pass
            raise

    _methodmap = MapProxy(dict(DefaultParser._methodmap) | {
        Marking.paren_open: '_read_from_paren_open',
        Constant: '_read_infix_predicated',
        Variable: '_read_infix_predicated'})

    def _read_operated(self, context: ParseContext, /) -> Operated:
        oper = Operator(context.value(context.current()))
        # only unary operators can be prefix operators
        if oper.arity != 1:
            raise ParseError(
                f"Unexpected non-prefix operator symbol '{context.current()}' "
                f"at position {context.pos}")
        context.advance()
        return oper(self._read(context))

    def _read_infix_predicated(self, context: ParseContext, /) -> Predicated:
        lhp = self._read_parameter(context)
        context.assert_current_in(Ctype.pred)
        ppos = context.pos
        try:
            pred = self._read_predicate(context)
        except UndefinedPredicateError as err:
            if not self.opts['auto_preds']:
                raise
            coords = err.coords
        else:
            arity = pred.arity
            if arity < 2:
                raise ParseError(
                    f"Unexpected infixed {arity}-ary predicate symbol at position {ppos}")
            return pred(lhp, *self._read_params(context, arity - 1))
        params = (lhp, *self._read_params_auto(context))
        arity = len(params)
        if arity < 2:
            raise ParseError(
                f"Unexpected infixed {arity}-ary predicate symbol at position {ppos}")
        try:
            pred = Predicate(*coords, arity)
        except ValueError as err:
            raise ParseError(
                f'Error auto-creating predicate {coords=} {arity=}: {err}')
        self.predicates.add(pred)
        return pred(params)

    def _read_from_paren_open(self, context: ParseContext, /) -> Operated:
        # if we have an open parenthesis, then we demand a binary infix operator sentence.
        # scan ahead to:
        #   - find the corresponding close parenthesis position
        #   - find the binary operator and its position
        oper = oper_pos = None
        depth = length = 1
        while depth:
            if not context.has_next(length):
                raise ParseError(
                    f'Unterminated open paren at position {context.pos}')
            peek = context.next(length)
            ptype = context.type(peek, None)
            if ptype is Marking.paren_close:
                depth -= 1
            elif ptype is Marking.paren_open:
                depth += 1
            elif ptype is Operator:
                peek_oper = Operator(context.value(peek))
                if peek_oper.arity == 2 and depth == 1:
                    oper_pos = context.pos + length
                    if oper is not None:
                        raise ParseError(
                            f'Unexpected {oper.name} symbol at position {oper_pos}')
                    oper = peek_oper
            length += 1
        if oper is None:
            raise ParseError(
                f'Missing binary operator at position {context.pos}')
        # now we can divide the string into lhs and rhs
        lhs_start = context.pos + 1
        # move past the open paren
        context.advance()
        # read the lhs
        lhs = self._read(context)
        context.chomp()
        if context.pos != oper_pos:
            raise ParseError(
                f'Invalid left side expression starting at position {lhs_start} '
                f'and ending at position {context.pos}, which proceeds past operator '
                f'({oper.name}) at position {oper_pos}')
        # move past the operator
        context.advance()
        # read the rhs
        rhs = self._read(context)
        context.chomp()
        # now we should have a close paren
        context.assert_current_is(Marking.paren_close)
        # move past the close paren
        context.advance()
        return oper(lhs, rhs)

class ParseTable(MapCover[str, Any]):
    'Parser table data class.'

    _instances: ClassVar[dict[Any, Self]] = {}

    @classmethod
    def load(cls, data: Mapping, /) -> Self:
        """Create and store instance from data.

        Args:
            data: The data mapping

        Raises:
            Emsg.DuplicateKey: on duplicate key

        Returns:
            The instance
        """
        notn = Notation[data['notation']]
        dialect = data.get('dialect', 'default')
        key = notn, dialect
        if key in cls._instances:
            raise Emsg.DuplicateKey(key)
        return cls._instances.setdefault(key, cls(data))

    @classmethod
    def fetch(cls, notation: Notation, dialect: str = None) -> Self:
        """Get a loaded instance.

        Args:
            notation: The notation
            dialect: The dialect. Default is 'default'.

        Returns:
            The instance
        """
        return cls._instances[Notation[notation], dialect or 'default']

    reversed: Mapping
    "Reversed mapping of item to symbol."

    __slots__ = ('reversed', 'notation', 'dialect')

    def __init__(self, data: Mapping, /):
        """
        Args:
            data: The table data.
        """
        self.notation = Notation[data['notation']]
        self.dialect = data.get('dialect', 'default')
        mapping = dict(data['mapping'])
        rev = dict(map(reversed, mapping.items()))
        for cls in (Operator, Quantifier, Predicate.System):
            for item in cls:
                rev.setdefault(item, rev[cls, item])
        for key, defaultkey in self._keydefaults.items():
            if defaultkey in rev:
                rev.setdefault(key, rev[defaultkey])
        self.reversed = MapProxy(rev)
        super().__init__(mapping)

    _keydefaults = MapProxy({
        Marking.whitespace: (Marking.whitespace, 0),
        Marking.paren_open: (Marking.paren_open, 0),
        Marking.paren_close: (Marking.paren_close, 0),
        (Predicate, Predicate.Existence): (Predicate.System, Predicate.Existence),
        (Predicate, Predicate.Identity): (Predicate.System, Predicate.Identity)})

    def __setattr__(self, name, value, /, *, sa = object.__setattr__):
        if getattr(self, name, NOARG) is not NOARG:
            raise AttributeError(name)
        sa(self, name, value)

    __delattr__ = Emsg.ReadOnly.razr
