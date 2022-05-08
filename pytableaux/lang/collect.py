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
"""
pytableaux.lang.collect
^^^^^^^^^^^^^^^^^^^^^^^

Language collection classes.
"""
from __future__ import annotations

import operator as opr
from itertools import repeat
from typing import TYPE_CHECKING, Any, Iterable, SupportsIndex

from pytableaux import tools, __docformat__, EMPTY_SET
from pytableaux.errors import Emsg, check
from pytableaux.lang import (LangCommonMeta, PredsItemRef, PredsItemSpec,
                             raiseae)
from pytableaux.lang.lex import LexicalAbc, Predicate, Sentence
from pytableaux.tools.abcs import abcm
from pytableaux.tools.decorators import lazy, membr, wraps
from pytableaux.tools.hybrids import qset
from pytableaux.tools.mappings import dmap
from pytableaux.tools.sequences import SequenceApi, seqf
from pytableaux.tools.typing import EnumDictType, IcmpFunc, IndexType

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'Argument',
    'ArgumentMeta',
    'Predicates',
)

NOARG = object()
EMPTY_IT = iter(EMPTY_SET)

class ArgumentMeta(LangCommonMeta):
    'Argument Metaclass.'

    def __call__(cls, *args, **kw):
        if len(args) == 1 and not len(kw) and isinstance(args[0], cls):
            return args[0]
        return super().__call__(*args, **kw)

class Argument(SequenceApi[Sentence], metaclass = ArgumentMeta):
    """Argument class.
    
    A container of sentences with sequence implementation, ordering and hashing.
    """

    def __init__(self,
        conclusion: Sentence,
        premises: Iterable[Sentence] = None,
        title: str = None
    ):
        self.seq = seqf(
            (Sentence(conclusion),) if premises is None
            else map(Sentence, (conclusion, *premises))
        )
        self.premises = seqf(self.seq[1:])
        if title is not None:
            check.inst(title, str)
        self.title = title

    __slots__ = 'seq', 'title', 'premises', '_hash', 

    sentences: seqf[Sentence]
    premises: seqf[Sentence]

    @property
    def conclusion(self) -> Sentence:
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

    @abcm.f.temp
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
            oper: IcmpFunc = getattr(opr, member.name)
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

    #******  Sequence Behavior

    def __len__(self):
        return len(self.seq)

    if TYPE_CHECKING:
        @overload
        def __getitem__(self, s: slice, /) -> seqf[Sentence]: ...

        @overload
        def __getitem__(self, i: SupportsIndex, /) -> Sentence: ...

    def __getitem__(self, index: IndexType, /):
        if isinstance(index, slice):
            return seqf(self.seq[index])
        return self.seq[index]

    @classmethod
    def _concat_res_type(cls, othrtype: type[Iterable], /):
        if issubclass(othrtype, Sentence):
            # Protect against adding an Operated sentence, which counts
            # as a sequence of sentences. It would add just the operands
            # but not the sentence.
            return NotImplemented
        return super()._concat_res_type(othrtype)

    @classmethod
    def _rconcat_res_type(cls, othrtype: type[Iterable], /):
        if issubclass(othrtype, Sentence):
            return NotImplemented
        if othrtype is tuple or othrtype is list:
            return othrtype
        return seqf

    @classmethod
    def _from_iterable(cls, it):
        '''Build an argument from an non-empty iterable using the first element
        as the conclusion, and the others as the premises.'''
        it = iter(it)
        try:
            conc = next(it)
        except StopIteration:
            raise TypeError('empty iterable') from None
        return cls(conc, it)

    #******  Other

    def for_json(self):
        'JSON Comptibility'
        return dict(
            conclusion = self.conclusion,
            premises = self.premises
        )

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

    __delattr__ = raiseae


class Predicates(qset[Predicate], metaclass = LangCommonMeta,
    hooks = {qset: dict(cast = Predicate)}
):
    'Predicate store. An ordered set with a multi-keyed lookup index.'

    _lookup: dmap[PredsItemRef, Predicate]
    __slots__ = '_lookup',

    def __init__(self, values: Iterable[PredsItemSpec] = None, /, *,
        sort: bool = False, key = None, reverse: bool = False):
        """Create a new store from an iterable of predicate objects
        or specs
        
        Args:
            values: Iterable of predicates or specs.
            sort: Whether to sort. Default is ``False``.
            key: Optional sort key function.
            reverse: Whether to reverse sort.
        """
        self._lookup = dmap()
        super().__init__(values)
        if sort:
            self.sort(key = key, reverse = reverse)

    def get(self, ref: PredsItemRef, default = NOARG, /) -> Predicate:
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
                return self.System[ref]
            except KeyError:
                pass
            if default is NOARG:
                raise
            return default

    def specs(self):
        return tuple(p.spec for p in self)

    @abcm.f.temp
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
            for other in filter(None, map(self._lookup.get, pred.refs)):
                if other != pred:
                    raise Emsg.ValueConflictFor(pred, pred.spec, other.spec)
            self._lookup |= zip(pred.refs, repeat(pred))
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

    #******  System Enum

    class System(Predicate.System):
        'System Predicates enum container class.'

        def __new__(cls, *spec):
            'Set the Enum value to the predicate instance.'
            return LexicalAbc.__new__(Predicate)

        @classmethod
        def _member_keys(cls, pred: Predicate):
            'Enum lookup index init hook. Add all predicate keys.'
            return super()._member_keys(pred) | pred.refs.union((pred,))

        @classmethod
        def _after_init(cls):
            'Enum after init hook. Set Predicate class attributes.'
            super()._after_init()
            for pred in cls:
                setattr(Predicate, pred.name, pred)
            Predicate.System = cls

        @abcm.f.before
        def expand(ns: EnumDictType, bases, **kw):
            'Inject members from annotations in Predicate.System class.'
            annots = abcm.annotated_attrs(Predicate.System)
            members = {
                name: spec for name, (vtype, spec)
                in annots.items() if vtype is Predicate
            }
            ns |= members
            ns._member_names += members.keys()


del(
    abcm,
    lazy,
    membr,
    opr,
    tools,
    wraps,
)