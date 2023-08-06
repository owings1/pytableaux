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
from collections.abc import Sequence
from itertools import repeat
from typing import Any, Iterable

from .. import __docformat__, tools
from ..errors import Emsg, check
from ..tools import abcs, lazy, membr, qset, wraps
from . import LangCommonMeta, Predicate, Sentence

__all__ = (
    'Argument',
    'ArgumentMeta',
    'Predicates')

NOARG = object()
EMPTY_IT = iter(())

class ArgumentMeta(LangCommonMeta):
    'Argument Metaclass.'

    def __call__(cls, *args, **kw):
        if len(args) == 1 and not len(kw) and isinstance(args[0], cls):
            return args[0]
        return super().__call__(*args, **kw)

class Argument(Sequence[Sentence], abcs.Copyable, immutcopy = True, metaclass = ArgumentMeta):
    """Argument class.
    
    A container of sentences (premises, conclusion) with sequence implementation,
    ordering and hashing.
    """

    def __init__(self, conclusion, premises = None, title = None):
        self.seq = tuple(
            (Sentence(conclusion),) if premises is None
            else map(Sentence, (conclusion, *premises)))
        self.premises = tuple(self.seq[1:])
        if title is not None:
            check.inst(title, str)
        self.title = title

    __slots__ = ('_hash', 'premises', 'seq', 'title')

    premises: tuple[Sentence, ...]
    "The argument's premises"

    @property
    def conclusion(self) -> Sentence:
        """The argument's conclusion."""
        return self.seq[0]

    @lazy.prop
    def hash(self) -> int:
        return hash(tuple(self))

    def predicates(self, **kw):
        """Return the predicates occuring in the argument.
        
        Args:
            **kw: sort keywords to pass to :class:`Predicates` constructor.
        
        Returns:
            Predicates: The predicates.
        """
        return Predicates((p for s in self for p in s.predicates), **kw)

    #******  Equality & Ordering

    # Two arguments are considered equal just when their conclusions are
    # equal, and their premises are equal (and in the same order). The
    # title is not considered in equality.

    @abcs.abcf.temp
    @tools.closure
    def ordr():

        sorder = Sentence.orderitems

        def cmpgen(a: Argument, b: Argument, /,):
            if a is b:
                yield 0
                return
            yield bool(a.conclusion) - bool(b.conclusion)
            yield len(a) - len(b)
            yield from (sorder(sa, sb) for sa, sb in zip(a, b))

        @membr.defer
        def ordr(member: membr):
            oper = getattr(opr, member.name)
            @wraps(oper)
            def f(self: Argument, other: Any, /):
                if not isinstance(other, Argument):
                    return NotImplemented
                for cmp in cmpgen(self, other):
                    if cmp:
                        break
                else:
                    cmp = 0
                return oper(cmp, 0)
            return f

        return ordr

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr() # type: ignore

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


class Predicates(qset[Predicate], metaclass = LangCommonMeta, hooks = {qset: dict(cast = Predicate)}):
    'Predicate store. An ordered set with a multi-keyed lookup index.'

    _lookup: dict[Any, Predicate]
    __slots__ = '_lookup',

    def __init__(self, values = None, /, *,
        sort: bool = False, key = None, reverse: bool = False):
        """Create a new store from an iterable of predicate objects
        or specs
        
        Args:
            values: Iterable of predicates or specs.
            sort: Whether to sort. Default is ``False``.
            key: Optional sort key function.
            reverse: Whether to reverse sort.
        """
        self._lookup = {}
        super().__init__(values)
        if sort:
            self.sort(key = key, reverse = reverse)

    def get(self, ref, default = NOARG, /) -> Predicate:
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

    @abcs.abcf.temp
    @qset.hook('done')
    def after_change(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
        'Implement after change (done) hook. Update lookup index.'
        for pred in leaving or EMPTY_IT:
            self._lookup -= pred.refs
            del(self._lookup[pred])
        for pred in arriving or EMPTY_IT:
            # Is there a distinct predicate that matches any lookup keys,
            # viz. BiCoords or name, that does not equal pred, e.g. arity
            # mismatch.
            for other in filter(None, map(self._lookup.get, refs := pred.refs)):
                if other != pred:
                    raise Emsg.ValueConflictFor(pred, pred.spec, other.spec)
            self._lookup |= zip(refs, repeat(pred))
            self._lookup[pred] = pred

    #******  Override qset

    def clear(self):
        super().clear()
        self._lookup.clear()

    def __contains__(self, ref, /):
        return ref in self._lookup

    def copy(self):
        inst = super().copy()
        inst._lookup = self._lookup.copy()
        return inst
