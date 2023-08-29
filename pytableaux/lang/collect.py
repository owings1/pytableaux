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
pytableaux.lang.collect
^^^^^^^^^^^^^^^^^^^^^^^

Language collection classes.
"""
from __future__ import annotations

import operator as opr
from collections import deque
from collections.abc import Sequence
from itertools import repeat, starmap
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Iterable

from ..errors import Emsg, ParseError, check
from ..tools import SequenceSet, abcs, group, lazy, membr, qset, qsetf, wraps
from . import LangCommonMeta, Lexical, Predicate, Sentence

if TYPE_CHECKING:
    from . import LexWriter, Parser

__all__ = (
    'Argument',
    'Predicates')

NOARG = object()

class ArgumentMeta(LangCommonMeta):
    'Argument Metaclass.'

    def __call__(cls, *args, **kw) -> Argument:
        if len(args) == 1 and not len(kw) and isinstance(args[0], cls):
            return args[0]
        return super().__call__(*args, **kw)

    _argstr_lw: LexWriter
    _argstr_pclass: type[Parser]
    _argstr_parser_empty: Parser

class Argument(Sequence[Sentence], abcs.Copyable, immutcopy=True, metaclass=ArgumentMeta):
    """Argument class.
    
    A container of sentences (premises, conclusion) with sequence implementation,
    ordering and hashing.

    Two arguments are considered equal just when their conclusions are
    equal, and their premises are equal (and in the same order). The
    title is not considered in equality.
    """

    def __init__(self, conclusion: Sentence, premises: Iterable[Sentence|None] = None, *, title: str|None = None):
        """
        Args:
            conclusion: The conclusion.
            premises: The premises or None.
        
        Keyword Args:
            title: An optional title.
        """
        self.seq = tuple(
            (Sentence(conclusion),) if premises is None
            else map(Sentence, (conclusion, *premises)))
        self.premises = tuple(self.seq[1:])
        if title is not None:
            check.inst(title, str)
        self.title = title

    __slots__ = ('_hash', 'premises', 'seq', 'title')

    conclusion: Sentence
    "The argument's conclusion."

    premises: tuple[Sentence, ...]
    "The argument's premises"

    title: str|None
    "Optional title"

    hash: int
    "The argument's hash."

    @property
    def conclusion(self) -> Sentence:
        return self.seq[0]

    @lazy.prop
    def hash(self) -> int:
        return hash(self.seq)

    def predicates(self, **kw):
        """Return the predicates occuring in the argument.
        
        Keyword Args:
            **kw: sort keywords to pass to :class:`Predicates` constructor.
        
        Returns:
            Predicates: The predicates.
        """
        return Predicates((p for s in self for p in s.predicates), **kw)

    def argstr(self) -> str:
        """Get the canonical string representation for recreating with
        :meth:`from_argstr()`.

        Returns:
            str: The argument string.
        """
        lw = __class__._argstr_lw
        preds = self.predicates(sort=True) - Predicate.System
        return '|'.join(
            filter(None, (
                ':'.join(map(lw, self)),
                ','.join(
                    '.'.join(map(str, p.spec)) for p in preds))))

    @staticmethod
    def from_argstr(argstr: str, /) -> Argument:
        """Construct an argument from the canonical string representation from
        :meth:`argstr()`.

        Args:
            argstr: The input string.

        Returns:
            Argument: The argument.

        Raises:
            ParseError
            TypeError
        """
        try:
            parts = deque(argstr.split('|'))
        except:
            check.inst(argstr, str)
            raise # pragma: no cover
        try:
            conc, *prems = parts.popleft().split(':')
        except IndexError:
            raise ParseError('Empty input')
        if parts:
            try:
                specsstr, = parts
            except ValueError:
                raise ParseError('Too many parts')
            try:
                preds = Predicates(
                    tuple(map(int, specstr.split('.')))
                    for specstr in specsstr.split(','))
            except Exception as err:
                raise ParseError(f'Error parsing predicates: {err}')
        else:
            preds = Predicates.EMPTY
        if len(preds):
            parser = __class__._argstr_pclass(predicates=preds)
        else:
            parser = __class__._argstr_parser_empty
        return parser.argument(conc, prems)

    #******  Equality & Ordering

    @abcs.abcf.temp
    @membr.defer
    def wrapper(member: membr):
        @wraps(oper := getattr(opr, member.name))
        def wrapped(self: Argument, other: Any, /):
            if self is other:
                return oper(0, 0)
            if not isinstance(other, Argument):
                return NotImplemented
            cmp = len(self) - len(other)
            if cmp:
                return oper(cmp, 0)
            for cmp in starmap(Lexical.orderitems, zip(self, other)):
                if cmp:
                    break
            return oper(cmp, 0)
        return wrapped

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = wrapper() # type: ignore

    def __hash__(self):
        return self.hash

    def __len__(self):
        return len(self.seq)

    def __getitem__(self, index, /):
        return self.seq[index]

    #******  Other

    def for_json(self):
        'JSON Comptibility'
        return dict(
            conclusion = self.conclusion,
            premises = self.premises)

    def __repr__(self):
        if self.title:
            desc = repr(self.title)
        else:
            desc = f'len({len(self)})'
        return f'<{type(self).__name__}:{desc}>'

    def __setattr__(self, attr, value):
        if hasattr(self, attr):
            raise AttributeError(attr)
        super().__setattr__(attr, value)

    __delattr__ = Emsg.ReadOnly.razr


class PredicatesBase(SequenceSet[Predicate], metaclass=LangCommonMeta):

    _lookup: dict[Any, Predicate]

    EMPTY: Predicates.Frozen

    def get(self, ref, /, default = NOARG) -> Predicate:
        """Get a predicate by any reference. Also searches system predicates.

        Args:
            ref: Predicate reference. See ``Predicate.ref``.
            default: Value to return if not found.

        Returns:
            The Predicate instance.

        Raises:
            KeyError: if missing and no default specified.
        """
        try:
            return self._lookup[ref]
        except KeyError:
            try:
                return Predicate.System[ref]
            except KeyError:
                pass
            if default is NOARG:
                raise
            return default

    def __contains__(self, ref, /):
        return ref in self._lookup

class Predicates(PredicatesBase, qset[Predicate]):
    """Predicate store. A sequenced set with a multi-keyed lookup index.

    Predicates with the same symbol coordinates (index, subscript) may
    have different arities. This class ensures that conflicting predicates are not
    in the same set, which is necessary, for example, for determinate parsing.
    """

    __slots__ = group('_lookup')

    def __init__(self, values=None, /, *, sort=False, key=None, reverse=False):
        """Create a new store from an iterable of predicate objects
        or specs
        
        Args:
            values: Iterable of predicates or specs.

        Keyword Args:
            sort: Whether to sort. Default is ``False``.
            key: Optional sort key function.
            reverse: Whether to reverse sort.
        """
        self._lookup = {}
        super().__init__(values)
        if sort:
            self.sort(key=key, reverse=reverse)

    def _hook_check(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
        'Implement before change (check) hook. Check for conflicting predicates.'
        # Is there a distinct predicate that matches any lookup keys,
        # viz. BiCoords or name, that does not equal pred, e.g. arity
        # mismatch.
        get = self._lookup.get
        conflicts: dict[Predicate, Predicate]|None = None
        for pred in arriving:
            for prior in filter(None, map(get, pred.refs)):
                if prior != pred:
                    if conflicts is None:
                        conflicts = {}
                    conflicts[prior] = pred
        if conflicts:
            for prior in leaving:
                conflicts.pop(prior, None)
                if not conflicts:
                    break
            else:
                for prior, pred in conflicts.items():
                    raise Emsg.ValueConflictFor(pred, pred.spec, prior.spec)

    def _hook_done(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
        'Implement after change (done) hook. Update lookup index.'
        lookup = self._lookup
        pop = lookup.pop
        for pred in leaving:
            for ref in pred.refs:
                pop(ref, None)
            pop(pred, None)
        update = lookup.update
        for pred in arriving:
            update(zip(pred.refs, repeat(pred)))
            lookup[pred] = pred

    def _hook_cast(self, value):
        return Predicate(value)

    def clear(self):
        super().clear()
        self._lookup.clear()

    def copy(self):
        inst = super().copy()
        inst._lookup = self._lookup.copy()
        return inst

    def frozen(self):
        return self.Frozen(self)

    class Frozen(PredicatesBase, qsetf[Predicate]):
        "Frozen :class:`Predicates` implentation."

        __slots__ = group('_lookup')

        def __init__(self, *args, **kw):
            v = Predicates(*args, **kw)
            super().__init__(v)
            self._lookup = MapProxy(v._lookup)

    wraps(__init__).write(Frozen.__init__)

PredicatesBase.EMPTY = Predicates.Frozen()