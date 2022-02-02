from __future__ import annotations

__all__ = 'SequenceSetApi', 'MutableSequenceSetApi', 'qsetf', 'qset'

from errors import (
    instcheck,
    # subclscheck,
    Emsg,
    DuplicateValueError,
    MissingValueError,
)
from tools.abcs import (
    abcf,
    abcm,
    abchook,
    MapProxy,
    T, VT, F
)
from tools.decorators import abstract, overload, final
from tools.sequences import (
    slicerange,
    SequenceApi,
    MutableSequenceApi,
    seqf,
    seqm,
    EMPTY_SEQ,
)
from tools.sets import (
    SetApi,
    MutableSetApi,
    setf,
    setm,
    EMPTY_SET,
)

from collections.abc import (
    Collection,
    # Set,
)
from itertools import (
    # chain,
    filterfalse
)
from typing import (
    Callable,
    Iterable,
    Iterator,
    Mapping,
    # MutableSequence,
    SupportsIndex,
    TypeVar
)

class SequenceSetApi(SequenceApi[VT], SetApi[VT]):
    'Sequence set (ordered set) read interface.  Comparisons follow Set semantics.'

    __slots__ = EMPTY_SET

    def count(self, value, /) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value, start = 0, stop = None, /) -> int:
        'Get the index of the value in the sequence.'
        if value not in self:
            raise MissingValueError(value)
        return super().index(value, start, stop)

    def __mul__(self, other):
        if isinstance(other, SupportsIndex):
            if int(other) > 1 and len(self) > 0:
                raise DuplicateValueError(self[0])
        return super().__mul__(other)

    __rmul__ = __mul__

    @abstract
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

class qsetf(SequenceSetApi[VT]):
    'Immutable sequence set implementation setf and seqf bases.'

    _set_: SetApi[VT]
    _seq_: SequenceApi[VT]

    __slots__ = '_set_', '_seq_'

    def __new__(cls, values: Iterable = None, /):
        self = object.__new__(cls)
        if values is None:
            self._seq_ = EMPTY_SEQ
            self._set_ = EMPTY_SET
        else:
            self._seq_ = seqf(dict.fromkeys(values))
            self._set_ = setf(self._seq_)
        return self

    def copy(self):
        inst = object.__new__(type(self))
        # copy reference only
        inst._seq_ = self._seq_
        inst._set_ = self._set_
        return inst

    def __len__(self):
        return len(self._seq_)

    def __contains__(self, value):
        return value in self._set_

    @overload
    def __getitem__(self: SeqSetT, index: slice) -> SeqSetT: ...

    @overload
    def __getitem__(self, index: SupportsIndex) -> VT: ...

    def __getitem__(self, index):
        if isinstance(index, SupportsIndex):
            return self._seq_[index]
        instcheck(index, slice)
        return self._from_iterable(self._seq_[index])

    def __iter__(self) -> Iterator[VT]:
        yield from self._seq_

    def __reversed__(self) -> Iterator[VT]:
        return reversed(self._seq_)

    def __repr__(self):
        return '%s({%s})' % (type(self).__name__, list(self._seq_).__repr__()[1:-1])


class MutableSequenceSetApi(SequenceSetApi[VT], MutableSequenceApi[VT], MutableSetApi[VT]):
    """Mutable sequence set (ordered set) interface.
    Sequence methods such as ``append`` raise ``DuplicateValueError``."""

    __slots__ = EMPTY_SET

    def add(self, value):
        'Append, catching ``DuplicateValueError``.'
        # Unlike discard() we try/except instead of pre-checking membership,
        # to allow for hooks to be called.
        try:
            self.append(value)
        except DuplicateValueError:
            pass

    def discard(self, value):
        'Remove if value is a member.'
        # Use contains check instead of try/except for set performance. 
        if value in self:
            self.remove(value)

    @abstract
    def reverse(self):
        'Reverse in place.'
        # Must re-implement MutableSequence method.
        raise NotImplementedError

SeqSetT = TypeVar('SeqSetT', bound = SequenceSetApi)

# SeqSetHookT = TypeVar('SeqSetHookT', bound = SequenceSetHooks)
MutSeqSetT  = TypeVar('MutSeqSetT',  bound = MutableSequenceSetApi)

class qset(MutableSequenceSetApi[VT]):
    'MutableSequenceSetApi implementation backed by built-in set and list.'

    _set_type_: type[setm] = setm
    _seq_type_: type[seqm] = seqm

    _set_: setm[VT]
    _seq_: seqm[VT]

    __slots__ = qsetf.__slots__

    def __new__(cls, *args, **kw):
        inst = object.__new__(cls)
        inst._set_ = cls._set_type_()
        inst._seq_ = cls._seq_type_()
        return inst

    def __init__(self, values: Iterable[VT] = None, /,):
        if values is not None: self |= values

    def copy(self):
        inst = object.__new__(type(self))
        inst._set_ = self._set_.copy()
        inst._seq_ = self._seq_.copy()
        return inst

    __len__      = qsetf.__len__
    __contains__ = qsetf.__contains__
    __getitem__  = qsetf[VT].__getitem__
    __iter__     = qsetf[VT].__iter__
    __reversed__ = qsetf[VT].__reversed__
    __repr__     = qsetf.__repr__

    @abcm.hookable('cast', 'check', 'done')
    # @abchook.cast
    # @abchook.check
    # @abchook.done
    def insert(self, index: SupportsIndex, value, /, *,
        cast = None, check = None, done = None
    ):
        'Insert a value before an index. Raises ``DuplicateValueError``.'

        # hook.cast
        if cast: value = cast(value)

        if value in self:
            raise DuplicateValueError(value)

        # hook.check
        check and check(self, (value,), EMPTY_SET)

        # --- begin changes -----
        self._seq_.insert(index, value)
        self._set_.add(value)
        # --- end changes -----

        # hook.done
        done and done(self, (value,), EMPTY_SET)

    @abcm.hookable('check', 'done')
    # @abchook.check
    # @abchook.done
    def __delitem__(self, key: SupportsIndex|slice, /, *,
        check = None, done = None
    ):
        'Delete by index/slice.'

        if isinstance(key, SupportsIndex):
            setdelete = self._set_.remove

        elif isinstance(key, slice):
            setdelete = self._set_.difference_update

        else:
            raise Emsg.InstCheck(key, (slice, SupportsIndex))

        # Retrieve the departing
        leaving = self[key]

        # hook.check
        check and check(self, EMPTY_SET, (leaving,))

        # --- begin changes -----
        del self._seq_[key]
        setdelete(leaving)
        # --- end changes -----

        # hook.done
        done and done(self, EMPTY_SET, (leaving,))

    @abcm.hookable('cast')
    # @abchook.cast
    def __setitem__(self, key: SupportsIndex|slice, value: VT|Collection[VT], /, *,
        cast = None
    ):
        'Set value by index/slice. Raises ``DuplicateValueError``.'

        if isinstance(key, SupportsIndex):
            # hook.cast
            if cast: value = cast(value)
            self.__setitem_index__(key, value)
            return

        if isinstance(key, slice):
            # hook.cast
            if cast: value = tuple(map(cast, value))
            else: instcheck(value, Collection)
            self.__setitem_slice__(key, value)
            return

        raise Emsg.InstCheck(key, (slice, SupportsIndex))

    @abcm.hookable('check', 'done')
    # @abchook.check
    # @abchook.done
    def __setitem_index__(self, index: SupportsIndex, arriving, /, *,
        check = None, done = None,
    ):
        'Index setitem Implementation'

        #  Retrieve the departing
        leaving = self._seq_[index]
    
        #  Check for duplicates
        if arriving in self and arriving != leaving:
            raise DuplicateValueError(arriving)

        # hook.check
        check and check(self, (arriving,), (leaving,))

        # --- begin changes -----

        # Remove from set
        self._set_.remove(leaving)
        try:
            # Assign by index to list.
            self._seq_[index] = arriving
        except:
            # On error, restore the set.
            self._set_.add(leaving)
            raise
        else:
            #  Add new value to the set
            self._set_.add(arriving)

        # --- end changes -----

        # hook.done
        done and done(self, (arriving,), (leaving,))

    @abcm.hookable('check', 'done')
    # @abchook.check
    # @abchook.done
    def __setitem_slice__(self, slice_: slice, arriving: Collection[VT], /, *,
        check = None, done = None,
    ):
        'Slice setitem Implementation'

        # Check length and compute range. This will fail for some bad input,
        # and it is fast to compute.
        range_ = slicerange(len(self), slice_, arriving)

        # Retrieve the departing.
        leaving = self[slice_]

        # Check for duplicates.
        # Any value that we already contain, and is not leaving with the others
        # is a duplicate.
        for v in filterfalse(leaving.__contains__, filter(self.__contains__, arriving)):
            raise DuplicateValueError(v)
        
        # hook.check
        check and check(self, arriving, leaving)

        # --- begin changes -----
        # Remove from set.
        self._set_ -= leaving
        try:
            # Assign by slice to list.
            self._seq_[slice_] = arriving
        except:
            # On error, restore the set.
            self._set_ |= leaving
            raise
        else:
            # Add new values to set.
            self._set_ |= arriving
        # --- end changes -----

        # hook.done
        done and done(self, arriving, leaving)

    def reverse(self):
        'Reverse in place.'
        self._seq_.reverse()

    def sort(self, /, *, key = None, reverse = False):
        'Sort the list in place.'
        self._seq_.sort(key = key, reverse = reverse)

    def clear(self):
        'Clear the list and set.'
        self._seq_.clear()
        self._set_.clear()


    # ---------- hook config ----------------- #

    # NB: This is an experimental feature, and will be moved to
    #     AbcMeta once generalized.
    #
    # TODO:
    #
    #   - Distinguish between declaring a hook for subclass use,
    #     and a subclass flagging a hook to process. Currently the
    #     @abchook decorator is used for both.
    #
    #   - Find a way to resolve hook name conflicts with different bases.
    #
    #   - Improve subclass init performance.

    _abchook_flagmask: abchook
    # hook name to method names
    _abc_hookinfo: Mapping[str, setf[str]]

    # @abcf.before
    @abcf.temp
    def setup_hooks(ns: dict, bases, **kw):
        info = {}
        mask = abchook.blank
        for flag in abchook:
            if not flag.value: continue
            methods = set()
            for name, member in ns.items():
                methodflag = abchook.get(member)
                if not methodflag.value: continue
                if flag in methodflag:
                    methods.add(name)
            if len(methods):
                info[flag.name] = setf(methods)
                mask |= flag
        ns['_abchook_flagmask'] = mask
        ns['_abc_hookinfo'] = MapProxy(info)

    def __init_subclass__(subcls: type[qset], **kw):
        'Subclass init. Check for hook config.'
        cls = __class__

        # Hooks listed in subclass declaration keyword 'qset'
        # hooks = kw.pop(cls.__name__, {}).get('hooks', {})
    
        super().__init_subclass__(**kw)
        return
        hookinfo = cls._abc_hookinfo
        hookmask = cls._abchook_flagmask
        ns = subcls.__dict__

        for member in ns.values():
            flag = abchook.get(member) & hookmask
            if not flag.value: continue
            for hookname in hookinfo:
                if abchook[hookname] in flag:
                    if hookname in hooks:
                        raise TypeError from Emsg.DuplicateKey(hookname)
                    hooks[hookname] = member
            continue

        if 0 and len(hooks):
            from tools.decorators import _copyf as copyf
            for hookname, hook in hooks.items():
                for method in hookinfo[hookname]:
                    func = getattr(subcls, method)
                    if method not in subcls.__dict__:
                        # Copy the function if subcls did not declare it,
                        # and, importantly, only once.
                        print('qset copyf', func)
                        func = copyf(func)
                        setattr(subcls, method, func)
                    kwdefs = func.__kwdefaults__
                    try:
                        defval = kwdefs[hookname]
                    except KeyError: raise TypeError
                    if defval is not None:
                        raise TypeError from Emsg.ValueConflictFor(hookname, hook, defval)
                    kwdefs[hookname] = hook

del(abstract, overload, final)