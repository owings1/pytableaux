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
pytableaux.tools.abcs
^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import abc as _abc
import enum as _enum
import functools
import itertools
import operator as opr
from collections.abc import Set
from typing import (TYPE_CHECKING, Annotated, Any, Callable, Collection,
                    Hashable, Iterable, Iterator, Mapping, Sequence,
                    SupportsIndex)

from pytableaux import __docformat__
from pytableaux import errors, tools
from pytableaux.errors import check
from pytableaux.tools.typing import (RT, TT, EbcT, EbcT2, EnumDictType, EnumT,
                                     F, Self, T)

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'Abc',
    'abcf',
    'abcm',
    'AbcMeta',
    'Copyable',
    'Ebc',
    'EbcMeta',
    'FlagEnum',
    'IntEnum',
)

KeysFunc = Callable[[Any], Set[Hashable]]
NOARG = object()

class Eset(frozenset, _enum.Enum):
    'Enum meta enumeration.'

    Empty = frozenset()

    member_key_methods = {'_member_keys'}
    reserve_names = {'seq', '_lookup', 'get',}
    hook_methods  = {'_member_keys', '_on_init', '_after_init'}
    clean_methods = hook_methods

@tools.classalias(_enum.auto)
class eauto:...

@tools.static
class ebcm:
    'Static Enum meta utils.'

    @staticmethod
    def fix_name_value(Class: type[EnumT], /) -> type[EnumT]:

        # cache attribute for flag enum.
        if callable(getattr(Class, '__invert__', None)):
            Class._invert_ = None # type: ignore

        # Clear DynCa from class layout
        Class.name  = None # type: ignore
        Class.value = None # type: ignore

        # Assign name & value directly.
        for member in Class:
            member.name = member._name_
            member.value = member._value_
        
        # Compatible as decorator.
        return Class

    @staticmethod
    def buildseq(Class: type[EnumT], /) -> tuple[EnumT, ...]:
        return tuple(
            map(Class._member_map_.__getitem__, Class._member_names_)
        )

    @staticmethod
    def clean_methods(Class: type[EnumT], /, *, deleter = type.__delattr__) -> type[EnumT]:
        for hname in filter(Class.__dict__.__contains__, Eset.clean_methods):
            deleter(Class, hname)
        return Class

    @staticmethod
    def is_enumcls(obj: Any) -> bool:
        return isinstance(obj, type) and issubclass(obj, _enum.Enum)

    @staticmethod
    def mixins(Class: type[_enum.Enum]) -> tuple[type, ...]:
        return *itertools.filterfalse(ebcm.is_enumcls, Class.__bases__),

    @staticmethod
    def rebase(oldcls: type[EnumT], *bases: type, ns: Mapping = None, metaclass: type = None, **kw) -> type[EnumT]:
        'Rebase an enum class with the same member data.'
        # Get metaclass.
        if metaclass is None:
            # Try the metaclass of the last enum class in the new bases.
            it = filter(ebcm.is_enumcls, reversed(bases))
            try:
                metaclass = type(next(it))
            except StopIteration:
                # Fall back on the old metaclass.
                metaclass = type(oldcls)
        # Validate metaclass.
        metaclass = check.subcls(check.inst(metaclass, type), _enum.EnumMeta)
        # New bases.
        if not len(bases):
            # If no new bases passed, try the last enum class of the old bases.
            it = filter(ebcm.is_enumcls, reversed(oldcls.__bases__))
            bases = list(it)[0:1]
            if not len(bases):
                # Fall back on built-in Enum.
                bases = _enum.Enum,
        # Reuse old non-enum bases.
        bases = ebcm.mixins(oldcls) + bases
        # Class name.
        clsname = oldcls.__name__
        # Prepare class dict.
        cdict = check.inst(metaclass.__prepare__(clsname, bases, **kw), dict)
        # Add member data from old class. Use _member_map_ to include aliases.
        for mname, m in oldcls._member_map_.items():
            # Use __setitem__, not update, else EnumDict won't work.
            cdict[mname] = m._value_
        if ns is not None:
            cdict.update(ns)
        # Create class.
        return metaclass(clsname, bases, cdict, **kw)


class EnumLookup(Mapping[Any, EnumT]):
    'Enum member lookup index.'

    if TYPE_CHECKING:
        @overload
        def build(self): # type: ignore
            "Build and update the whole index."

        @overload
        def pseudo(self, member: EnumT, /) -> EnumT: # type: ignore
            "Add a single pseudo member to the index."

    __slots__ = (
        '__len__', '__getitem__', '__iter__', '__reversed__',
        'build', 'pseudo'
    )

    def __init__(self, Owner: type[EnumT], /, *funcs: KeysFunc, build = False):

        if hasattr(self, 'build'):
            raise TypeError

        keyfuncs = {self._default_keys}
        keyfuncs.update(funcs)
        for meth in Eset.member_key_methods:
            func = getattr(Owner, meth, None)
            if callable(func):
                keyfuncs.add(func)

        source = {}

        setitem = source.__setitem__

        def _pseudo(member: EnumT) -> EnumT:
            for key in self._check_pseudo(member, Owner):
                setitem(key, member)
            return member

        def _build():
            builder = self._makemap(Owner, keyfuncs)
            source.clear()
            source.update(builder)
            return self

        self._srcinit(source, self, _build, _pseudo)
        if build:
            _build()

    @staticmethod
    def _srcinit(src: Any, dest: Any, build: Callable, pseudo: Callable, /, *,
        ga = object.__getattribute__,
        sa = object.__setattr__,
        names = tuple(filter(tools.isdund, __slots__))
    ) -> None:
        "Initialize instance mapping and closure attributes."
        for name in names:
            sa(dest, name, ga(src, name))
        sa(dest, 'build', build)
        sa(dest, 'pseudo', pseudo)

    @classmethod
    def _makemap(cls, Owner: type[EnumT], keyfuncs: Collection[KeysFunc], /) -> dict[Hashable, EnumT]:
        "Build an index source dictionary."

        # Named members, including aliases, but not pseudos.
        member_map = Owner._member_map_
        # Canonical names, no aliases.
        canon_names = Owner._member_names_
        # Unique members, including unnamed (pseudos), but not aliases.
        unique_members = set(Owner._value2member_map_.values())

        # Canonical members, named, unique, and ordered.
        member_seq = tuple(map(member_map.get, canon_names))
        # Unnamed (pseudo) members.
        pseudos = unique_members.difference(member_map.values())
        # Alias names
        aliases = set(member_map).difference(canon_names)

        builder = cls._seqmap(member_seq, keyfuncs)

        if len(pseudos):
            builder |= cls._pseudomap(pseudos)
        if len(aliases):
            builder |= {alias: member_map[alias] for alias in aliases}

        return builder

    @classmethod
    def _seqmap(cls,
        members: Sequence[EnumT], keyfuncs: Collection[KeysFunc], /) -> dict[Hashable, EnumT]:
        """Build the main index map for the sequence of proper (named) members
        with the given keys functions.
        """
        return {
            key : member
            for member_keys, member in zip(
                ({key for func in keyfuncs for key in func(member)}
                    for member in members),
                members
            ) for key in member_keys
        }

    @classmethod
    def _pseudomap(cls, pseudos: Collection[EnumT], /) -> dict[Hashable, EnumT]:
        """Build a restricted index map for pseudo (unnamed) members, e.g.
        dynamic bit flag values. Only value and instance keys are used.
        """
        getkeys = cls._pseudo_keys
        return {key: entry
            for pseudo_keys, entry in (
                (getkeys(pseudo), pseudo)
                for pseudo in pseudos
            ) for key in pseudo_keys
        }

    @classmethod
    def _check_pseudo(cls, pseudo: EnumT, Owner: type[EnumT], /) -> set[Hashable]:
        "Verify a pseudo member, returning index keys."
        check = Owner._value2member_map_[pseudo._value_]
        if check is not pseudo:
            raise TypeError from errors.Emsg.ValueConflict(pseudo, check)
        if pseudo._name_ is not None:
            raise TypeError from errors.Emsg.WrongValue(pseudo._name_, None)
        return cls._pseudo_keys(pseudo)

    @staticmethod
    def _pseudo_keys(pseudo: _enum.Enum, /) -> set[Hashable]:
        'Pseudo member lookup keys'
        return {pseudo, pseudo._value_}

    @staticmethod
    def _default_keys(member: _enum.Enum, /) -> set[Hashable]:
        'Default member lookup keys'
        return {member._name_, (member._name_,), member, member._value_}

    def _asdict(self) -> dict[Any, EnumT]:
        'Compatibility for JSON serialization.'
        return dict(self)

    def __setattr__(self, name, value):
        raise errors.Emsg.ReadOnly(self, name)

    def __delattr__(self, name):
        raise errors.Emsg.ReadOnly(self, name)

    def __repr__(self):
        return repr(self._asdict())


#=============================================================================
#_____________________________________________________________________________
#
#       Enum Meta
#_____________________________________________________________________________



class EbcMeta(_enum.EnumMeta, type[EbcT2]):
    'General-purpose base Metaclass for all Enum classes.'

    #******  Class Instance Variables

    if TYPE_CHECKING:
        @property
        @overload
        def seq(self: type[EbcT]) -> Sequence[EbcT]: ...

    seq     : Sequence[EbcT2]
    _lookup : EnumLookup[EbcT2]

    _member_names_ : Sequence[str]
    _member_map_   : Mapping[str, EbcT2]
    _mixin_bases_  : tuple[type, ...]

    #******  Class Creation

    @classmethod
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw):
        ns: EnumDictType = super().__prepare__(clsname, bases, **kw)
        return ns

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: EnumDictType, /, *,
        skipflags = False, noidxbuild = False, skipabcm = False, **kw
    ):
        if not skipabcm:
            # Run generic Abc init hooks.
            abcm.nsinit(ns, bases, skipflags = skipflags)

        forbid = Eset.reserve_names.intersection(ns)
        if forbid:
            raise TypeError(f'Restricted names: {forbid}')

        # Create class.
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        # Store mixin bases
        Class._mixin_bases_ = ebcm.mixins(Class)

        if not skipabcm:
            # Run generic Abc after hooks.
            abcm.clsafter(Class, ns, skipflags = skipflags)

        # Freeze Enum class attributes.
        Class._member_map_ = tools.MapProxy(Class._member_map_)
        Class._member_names_ = tuple(Class._member_names_)

        if not len(Class):
            # No members to process.
            Class._after_init()
            return Class

        # Store the fixed member sequence. Necessary for iterating.
        Class.seq = ebcm.buildseq(Class)

        # Performance tweaks.
        ebcm.fix_name_value(Class)

        # Init hook to process members before index is created.
        Class._on_init(Class)

        # Create index.
        Class._lookup = EnumLookup(Class, build = not noidxbuild)

        # After init hook.
        Class._after_init()

        # Cleanup.
        ebcm.clean_methods(Class)

        return Class

    #******  Subclass Init Hooks

    def _member_keys(cls, member: Ebc,/) -> Set[Hashable]:
        'Init hook to get the index lookup keys for a member.'
        return Eset.Empty

    def _on_init(cls, subcls: type[EbcT]|EbcMeta,/):
        '''Init hook after all members have been initialized, before index
        is created. **NB:** Skips abstract classes.'''
        pass

    def _after_init(cls):
        'Init hook once the class is initialized. Includes abstract classes.'
        pass

    #******  Class Call

    def __call__(cls: type[EbcT]|EbcMeta[EbcT2], value: Any, names = None, **kw) -> EbcT:
        if names is not None:
            return super().__call__(value, names, **kw)
        try:
            return cls._lookup[value]
        except KeyError:
            pass
        # Will raise ValueError for bad value.
        member = cls.__new__(cls, value) # type: ignore
        # It must be a pseudo member, since it was not in _lookup.
        return cls._lookup.pseudo(member)

    #******  Mapping(ish) Behavior

    def get(cls: type[EbcT]|EbcMeta[EbcT2], key: Any, default: Any = NOARG, /) -> EbcT|EbcT2:
        """Get a member by an indexed reference key.

        Args:
            key: member lookup key, value, instance, etc..
            default: value to return if not found.

        Returns:
            The enum member, or default if specified and not found.

        Raises:
            KeyError: if not found and no default specified.
        """
        try:
            return cls._lookup[key]
        except KeyError:
            if default is NOARG:
                raise
            return default

    def __getitem__(cls: type[EbcT]|EbcMeta[EbcT2], key: Any, /) -> EbcT|EbcT2:
        return cls._lookup[key]

    def __contains__(cls, key: Any, /):
        return key in cls._lookup

    #******  Sequence(ish) Behavior

    def __iter__(cls: type[EbcT]|EbcMeta[EbcT2]) -> Iterator[EbcT|EbcT2]:
        return iter(cls.seq)

    def __reversed__(cls: type[EbcT]|EbcMeta[EbcT2]) -> Iterator[EbcT|EbcT2]:
        return reversed(cls.seq)

    #******  Misc Behaviors

    def __getattr__(cls, name, /):
        raise AttributeError(name)

    def __dir__(cls):
        return cls._member_names_

    @property
    def __members__(cls):
        # Override to not double-proxy
        return cls._member_map_

#=============================================================================
#_____________________________________________________________________________
#
#       Ebc Support Classes
#
#           skipflags = True
#           skipabcm = True
#_____________________________________________________________________________

class Ebc(_enum.Enum, metaclass = EbcMeta, skipflags = True, skipabcm = True):

    __slots__ = Eset.Empty

    name  : str
    value : Any

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    @classmethod
    def _on_init(cls: EbcMeta, subcls: type[Ebc]):
        'Propagate hook up to metaclass.'
        type(cls)._on_init(cls, subcls)

    @classmethod
    def _member_keys(cls: EbcMeta, member: Ebc):
        'Propagate hook up to metaclass.'
        return type(cls)._member_keys(cls, member)

    @classmethod
    def _after_init(cls: EbcMeta):
        'Propagate hook up to metaclass.'
        type(cls)._after_init(cls)

    def __repr__(self):
        clsname = type(self).__name__
        mixins = getattr(self, '_mixin_bases_', None)
        try:
            s = f'{clsname}.{self._name_}'
            if mixins:
                mfn = mixins[0].__repr__
                return f'<{s}:{mfn(self._value_)}>'
            return f'<{s}>'
        except AttributeError:
            return f'<{clsname}.?ERR?>'

class Astr(str, Ebc, skipflags = True, skipabcm = True):

    flag     = '_abc_flag'
    hookuser = '_abc_hook_user'
    hookinfo = '_abc_hook_info'

class FlagEnum(_enum.Flag, Ebc, skipflags = True, skipabcm = True):

    name  : str|None
    value : int

    _invert_ : tuple[int, FlagEnum]

    @classmethod
    def _missing_(cls, value: Any):
        member: FlagEnum = super()._missing_(value)
        member.value = member._value_
        member.name  = member._name_
        return member

    def __invert__(self):
        cached = self._invert_
        value = self.value
        if cached is not None and cached[0] == value:
            return cached[1]
        other = super().__invert__()
        self._invert_ = value, other
        other._invert_ = other.value, self
        return other

class abcf(FlagEnum, skipflags = True, skipabcm = True):
    'Enum flag for AbcMeta functionality.'

    __slots__ = 'name', 'value', '_value_', '_invert_'

    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32
    inherit = 64

    _cleanable = before | temp | after

    def __call__(self, obj: F) -> F:
        """Add the flag to obj's meta flag with bitwise OR. Return obj for
        decorator use."""
        return self.save(obj, self | self.read(obj))

    @classmethod
    def read(cls, obj, default: abcf|int = 0, /, *, attr = Astr.flag) -> abcf:
        "Get the flag (or `blank`) for any obj."
        return getattr(obj, attr, cls(default))

    @classmethod
    def save(cls, obj: F, value: abcf|int, /, *, attr = Astr.flag) -> F:
        'Write the value, returns obj for decorator use.'
        setattr(obj, attr, cls(value))
        return obj

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Meta
#_____________________________________________________________________________

@tools.static
class abcm:
    'Static Abc meta util functions.'

    @tools.classalias(abcf)
    class f: pass

    _frozenset: type[frozenset] = frozenset

    @staticmethod
    def nsinit(ns: dict, bases, /, skipflags = False):
        'Class namespace prepare routine.'
        # iterate over copy since hooks may modify ns.
        if not skipflags:
            for member in tuple(ns.values()):
                mf = abcf.read(member)
                if mf.before in mf:
                    member(ns, bases)
        # cast slots to a set
        slots = ns.get('__slots__')
        if isinstance(slots, Iterable) and not isinstance(slots, Set):
            ns['__slots__'] = abcm._frozenset(slots)

    @staticmethod
    def clsafter(Class: TT, ns: Mapping = None, /, skipflags = False,
        deleter = type.__delattr__) -> TT:
        'After class init routine.'
        # Allow use as standalone class decorator
        if ns is None:
            ns = Class.__dict__.copy()
        todelete = set()
        if not skipflags:
            for name, member in ns.items():
                # Finish calling the 'after' hooks before anything else, since
                # they might modify other meta config.
                mf = abcf.read(member)
                if mf is not mf.blank and mf in mf._cleanable:
                    if mf.after in mf:
                        member(Class)
                    todelete.add(name)
        for name in todelete:
            deleter(Class, name)
        return Class

    @staticmethod
    def isabstract(obj):
        if isinstance(obj, type):
            return bool(len(getattr(obj, '__abstractmethods__', Eset.Empty)))
        return bool(getattr(obj, '__isabstractmethod__', False))

    @staticmethod
    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        # This is called infrequently, so we import lazily.
        from typing import get_args, get_origin, get_type_hints
        annot = get_type_hints(obj, include_extras = True)
        return {
            k: get_args(v) for k,v in annot.items()
            if get_origin(v) is Annotated
        }

    @staticmethod
    def check_mrodict(mro: Sequence[type], *names: str):
        'Check whether methods are implemented for dynamic subclassing.'
        if len(names) and not len(mro):
            return NotImplemented
        for name in names:
            for base in mro:
                if name in base.__dict__:
                    if base.__dict__[name] is None:
                        return NotImplemented
                    break
            else:
                return NotImplemented
        return True

    @staticmethod
    def merge_mroattr(subcls: type, name: str, *args, setter = setattr, **kw):
        value = abcm.merged_mroattr(subcls, name, *args, **kw)
        setter(subcls, name, value)
        return value

    @staticmethod
    def merged_mroattr(subcls: type, name: str, /,
        default: T = NOARG,
        oper = opr.or_,
        *,
        initial: T = NOARG,
        transform: Callable[[T], RT] = tools.thru,
        **iteropts
    ) -> RT:
        it = abcm.mroiter(subcls, **iteropts)
        if default is NOARG:
            it = (getattr(c, name) for c in it)
        else:
            it = (getattr(c, name, default) for c in it)
            if initial is NOARG:
                initial = default
        if initial is NOARG:
            value = functools.reduce(oper, it)
        else:
            value = functools.reduce(oper, it, initial)
        return transform(value)

    @staticmethod
    def mroiter(subcls: type, /, supcls: type|tuple[type, ...] = None, *,
        mcls: type|tuple[type, ...] = None,
        reverse = True, start: SupportsIndex = None, stop: SupportsIndex = None,
    ) -> Iterable[type]:
        it = subcls.mro()
        if reverse:
            it = reversed(it)
        else:
            it = iter(it)
        if mcls is not None:
            it = filter(lambda c: isinstance(c, mcls), it)
        if supcls is not None:
            it = filter(lambda c: issubclass(c, supcls), it)
        if start is not None or stop is not None:
            it = itertools.islice(it, start, stop) # type: ignore
        return it

    @staticmethod
    def hookable(*hooks: str, attr = Astr.hookinfo):
        'Decorator factory for specifying available hooks (provider).'
        def decorator(func: F) -> F:
            value = getattr(func, attr, None)
            if value is None:
                value = set()
                setattr(func, attr, value)
            value.update(hooks)
            return func
        return decorator

    @staticmethod
    def hookinfo(Class: type):
        from pytableaux.tools.hooks import hookutil
        return hookutil.provider_info(Class)


class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, /,
        hooks = None,
        skiphooks = False,
        skipflags = False,
        hookinfo = None,
        **kw
    ):
        abcm.nsinit(ns, bases, skipflags = skipflags)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        if not skiphooks:
            from pytableaux.tools.hooks import hookutil
            hookutil.init_user(Class, hooks)
        abcm.clsafter(Class, ns, skipflags = skipflags)
        if not skiphooks:
            hookutil.init_provider(Class, hookinfo)
        return Class

    def hook(cls, *hooks: str, attr = Astr.hookuser):
        'Decorator factory for tagging hook implementation (user).'
        def decorator(func: F) -> F:
            value = getattr(func, attr, None)
            if value is None:
                value = dict()
                setattr(func, attr, value)
            impl = value.setdefault(cls, {})
            for name in hooks:
                if name in impl:
                    raise TypeError from errors.Emsg.DuplicateKey(name)
                impl[name] = func
            return func
        return decorator

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Base Classes
#
#           skiphooks = True
#_____________________________________________________________________________

class Abc(metaclass = AbcMeta, skiphooks = True):
    'Convenience for using AbcMeta as metaclass.'

    __slots__ = Eset.Empty

class Copyable(Abc, skiphooks = True):

    __slots__ = Eset.Empty

    @tools.abstract
    def copy(self: Self) -> Self:
        cls = type(self)
        return cls.__new__(cls)

    __copy__ = copy

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return abcm.check_mrodict(subcls.mro(), '__copy__', 'copy')

    def __init_subclass__(subcls: type[Copyable], **kw):
        "Subclass init hook. Set `__copy__()` to `copy()`."
        super().__init_subclass__(**kw)
        subcls.__copy__ = subcls.copy

#=============================================================================
#_____________________________________________________________________________
#
#       Enum Base Classes
#_____________________________________________________________________________

class IntEnum(int, Ebc):
    __slots__ = Eset.Empty
    # NB: "nonempty __slots__ not supported for subtype of 'IntEnum'"
    pass

class IntFlag(int, FlagEnum):
    __slots__ = Eset.Empty
    # NB: slots must be empty for int (layout conflict)
    pass

#=============================================================================
#_____________________________________________________________________________
#
#       Rebases
#_____________________________________________________________________________

Eset = ebcm.rebase(Eset, Ebc)
