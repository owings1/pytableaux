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
from itertools import repeat, starmap
from typing import TYPE_CHECKING, Any, Iterable

from .. import tools
from ..errors import Emsg, check
from ..tools import abcs, group, lazy, membr, qset, wraps
from . import LangCommonMeta, Predicate, Sentence

if TYPE_CHECKING:
    from . import PolishLexWriter, PolishParser

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

    _keystr_lw: PolishLexWriter
    _keystr_pclass: type[PolishParser]

    def make_keystr(self, inst: Argument) -> str:
        try:
            lw = self._keystr_lw
        except AttributeError:
            from .writing import PolishLexWriter
            type.__setattr__(self, '_keystr_lw', PolishLexWriter(format='text', dialect='ascii'))
            lw = self._keystr_lw
        preds = inst.predicates() - Predicate.System
        preds.sort()
        specstrs = ('.'.join(map(str, p.spec)) for p in preds)
        return '|'.join(filter(None, (':'.join(map(lw, inst)), ','.join(specstrs))))

    def from_keystr(self, keystr: str) -> Argument:
        try:
            pclass = self._keystr_pclass
        except AttributeError:
            from .parsing import PolishParser
            type.__setattr__(self, '_keystr_pclass', PolishParser)
            pclass = self._keystr_pclass
        preds = Predicates()
        parts = keystr.split('|')
        conc, *prems = parts.pop(0).split(':')
        if parts:
            specsstr, = parts
            for specstr in specsstr.split(','):
                preds.add(tuple(map(int, specstr.split('.'))))
        return pclass(preds).argument(conc, prems)

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
        
        Kwargs:
            title: An optional title or None.
        """
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
    title: str|None
    "Optional title"

    @property
    def conclusion(self) -> Sentence:
        "The argument's conclusion."
        return self.seq[0]

    @lazy.prop
    def hash(self) -> int:
        "The argument's hash. Does not consider title."
        return hash(self.seq)

    def predicates(self, **kw):
        """Return the predicates occuring in the argument.
        
        Args:
            **kw: sort keywords to pass to :class:`Predicates` constructor.
        
        Returns:
            Predicates: The predicates.
        """
        return Predicates((p for s in self for p in s.predicates), **kw)

    #******  Equality & Ordering

    @abcs.abcf.temp
    @tools.closure
    def ordr():

        def cmpgen(a: Argument, b: Argument, /,):
            if a is b:
                yield 0
                return
            yield len(a) - len(b)
            yield from starmap(Sentence.orderitems, zip(a, b))

        @membr.defer
        def wrapper(member: membr):
            @wraps(oper := getattr(opr, member.name))
            def wrapped(self: Argument, other: Any, /):
                if not isinstance(other, Argument):
                    return NotImplemented
                for cmp in cmpgen(self, other):
                    if cmp:
                        break
                return oper(cmp, 0)
            return wrapped

        return wrapper

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

    def keystr(self):
        return __class__.make_keystr(self)

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


class Predicates(qset[Predicate], metaclass=LangCommonMeta, hooks={qset: dict(cast=Predicate)}):
    """Predicate store. A sequenced set with a multi-keyed lookup index.

    Predicates with the same symbol coordinates (index, subscript) may
    have different arities. This class ensures that conflicting predicates are not
    in the same set, which is necessary, for example, for determinate parsing.
    """

    _lookup: dict[Any, Predicate]
    __slots__ = group('_lookup')

    def __init__(self, values=None, /, *, sort=False, key=None, reverse=False):
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
            self.sort(key=key, reverse=reverse)

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
    @qset.hook('check')
    def before_change(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
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

    @abcs.abcf.temp
    @qset.hook('done')
    def after_change(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
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
