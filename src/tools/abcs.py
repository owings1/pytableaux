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
# pytableaux - tools.abcs module
from __future__ import annotations

if 'Exports' or True:

    __all__ = (
        'abcf',
        'abcm',

        'AbcMeta',
        'AbcEnumMeta',

        'Abc',
        'Copyable',

        'AbcEnum',
        'FlagEnum',
        'IntEnum',
        'MapProxy',

        # 'final',
        # 'overload',
        # 'abstract',
        # 'static',
    )

if 'Imports' or True:

    # No local imports

    import abc as _abc
    from collections.abc import Set
    import enum as _enum
    # exportable
    from enum import auto as eauto
    from functools import reduce
    from itertools import chain, islice
    import operator as opr
    from types import (
        FunctionType,
        MappingProxyType as _MapProxy,
    )
    from typing import (
        # exportable imports
        final, overload,

        # Annotations
        Any,
        Annotated,
        Callable,
        Collection,
        Generic,
        Hashable,
        Iterable,
        Iterator,
        Mapping,
        NamedTuple,
        Sequence,
        SupportsIndex,
        ParamSpec,
        TypeVar,
    )

if 'Type Variables' or True:

    T  = TypeVar('T')
    T1 = TypeVar('T1')
    T2 = TypeVar('T2')

    # Key type
    KT = TypeVar('KT')

    # Value type
    VT = TypeVar('VT')

    # Return type
    RT = TypeVar('RT')

    # Self type
    Self = TypeVar('Self')

    T_co  = TypeVar('T_co',  covariant = True)
    KT_co = TypeVar('KT_co', covariant = True)
    VT_co = TypeVar('VT_co', covariant = True)
    T_contra = TypeVar('T_contra', contravariant = True)

    # Callable bound, use for decorator, etc.
    F   = TypeVar('F',  bound = Callable[..., Any])

    # Exception bound
    ExT = TypeVar('ExT', bound = Exception)

    # Type bound, use for class decorator, etc.
    TT    = TypeVar('TT',    bound = type)
    TT_co = TypeVar('TT_co', bound = type, covariant = True)

    P = ParamSpec('P')

    EnT  = TypeVar('EnT',  bound = 'AbcEnum')
    EnT2 = TypeVar('EnT2', bound = 'AbcEnum')
    # EnT_co     = TypeVar('EnT_co', bound = 'AbcEnum', covariant = True)
    EnFlagT = TypeVar('EnFlagT', bound = 'FlagEnum')
    EnKeyFunc = Callable[['AbcEnum'], Set[Hashable]]

    IndexType = SupportsIndex | slice
    NotImplType = type(NotImplemented)

if 'Decorators & Utils' or True:

    def _thru(obj: T) -> T: return obj
    def _isdund(name):
        return (
            len(name) > 4 and name[:2] == name[-2:] == '__' and
            name[2] != '_' and name[-3] != '_'
        )
    # Global decorators. Re-exported by decorators module.

    from abc import abstractmethod as abstract

    @overload
    def static(cls: TT, /) -> TT: ...

    @overload
    def static(meth: Callable[..., T], /) -> staticmethod[T]: ...

    def static(cls, /):
        'Static class decorator wrapper around staticmethod'

        if not isinstance(cls, type):
            if isinstance(cls, (classmethod, staticmethod)):
                return cls
            # instcheck(cls, Callable)
            return staticmethod(cls)

        ns = cls.__dict__

        for name, member in ns.items():
            if _isdund(name) or not isinstance(member, FunctionType):
                continue
            setattr(cls, name, staticmethod(member))

        cname = cls.__name__
        debug = cname =='opercache'
        if '__new__' not in ns:
            debug and print(cname, '__new__ not in ns')
            cls.__new__ = _thru # type: ignore

        if '__init__' not in ns:
            debug and print(cname, '__init__ not in ns')
            def finit(self): raise TypeError
            cls.__init__ = finit

        return cls

    def closure(func: Callable[..., T]) -> T:
        return func()

if 'Util Classes' or True:

    class MapProxy(Mapping[KT, VT]):
        'Cast to a proxy if not already.'
        EMPTY_MAP = _MapProxy({})

        def __new__(cls, mapping: Mapping[KT, VT] = None) -> MapProxy[KT, VT]:

            if mapping is None:
                return cls.EMPTY_MAP # type: ignore
            if isinstance(mapping, _MapProxy):
                return mapping # type: ignore
            if not isinstance(mapping, Mapping):
                mapping = dict(mapping)
            return _MapProxy(mapping) # type: ignore

    class _EnumEntry(NamedTuple):
        'The value of the enum lookup index.'
        member : AbcEnum
        index  : int | None
        nextmember: AbcEnum | None

    class EnumEntry(_EnumEntry, Generic[EnT]):
        'The value of the enum lookup index.'
        __slots__ = ()
        member : EnT
        index  : int | None
        nextmember: EnT | None

    class EnumDictType(_enum._EnumDict):
        'Stub type for annotation reference.'
        _member_names: list[str]
        _last_values : list[object]
        _ignore      : list[str]
        _auto_called : bool
        _cls_name    : str

if 'Constants' or True:

    ABC_FLAG_ATTR     = '_abc_flag'
    ABC_HOOKUSER_ATTR = '_abc_hook_user'
    ABC_HOOKINFO_ATTR = '_abc_hook_info'

    ENUM_RESERVE_NAMES = frozenset(
        {'seq', '_lookup', 'get',}
    )
    ENUM_HOOK_METHODS = frozenset(
        {'_member_keys', '_on_init', '_after_init'}
    )
    ENUM_CLEAN_METHODS = ENUM_HOOK_METHODS

    _EMPTY = ()
    _EMPTY_SET = frozenset()
    # _EMPTY_MAP = MapProxy[Any, Any]()
    _NOARG = object()
    # _NOGET = object()

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Meta
#_____________________________________________________________________________

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
            from tools.hooks import hookutil
            hookutil.init_user(Class, hooks)
        abcm.clsafter(Class, ns, skipflags = skipflags)
        if not skiphooks:
            hookutil.init_provider(Class, hookinfo)
        return Class

    def hook(cls, *hooks: str, attr = ABC_HOOKUSER_ATTR):
        'Decorator factory for tagging hook implementation (user).'
        def decorator(func: F) -> F:
            value = getattr(func, attr, None)
            if value is None:
                value = dict()
                setattr(func, attr, value)
            impl = value.setdefault(cls, {})
            for name in hooks:
                if name in impl:
                    from errors import Emsg
                    raise TypeError from Emsg.DuplicateKey(name)
                impl[name] = func
            return func
        return decorator

@static
class abcm:
    'Static meta util functions.'

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
            return bool(len(getattr(obj, '__abstractmethods__', _EMPTY)))
        return bool(getattr(obj, '__isabstractmethod__', False))

    @staticmethod
    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        # This is called infrequently, so we import lazily.
        from typing import get_type_hints, get_args, get_origin
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
        default: T = _NOARG,
        oper = opr.or_,
        *,
        initial: T = _NOARG,
        transform: Callable[[T], RT] = _thru,
        **iteropts
    ) -> RT:
        it = abcm.mroiter(subcls, **iteropts)
        if default is _NOARG:
            it = (getattr(c, name) for c in it)
        else:
            it = (getattr(c, name, default) for c in it)
            if initial is _NOARG:
                initial = default
        if initial is _NOARG:
            value = reduce(oper, it)
        else:
            value = reduce(oper, it, initial)
        return transform(value)

    @staticmethod
    def mroiter(subcls: type, /, supcls: type|tuple[type, ...] = None,
        *,
        reverse = True, start: SupportsIndex = None, stop: SupportsIndex = None,
    ) -> Iterable[type]:
        it = subcls.mro()
        if reverse:
            it = reversed(it)
        else:
            it = iter(it)
        if supcls is not None:
            it = filter(lambda c: issubclass(c, supcls), it)
        if start is not None or stop is not None:
            it = islice(it, start, stop) # type: ignore
        return it

    @staticmethod
    def hookable(*hooks: str, attr = ABC_HOOKINFO_ATTR):
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
        from tools.hooks import hookutil
        return hookutil.provider_info(Class)
        # return HookInfo(Class)

#=============================================================================
#_____________________________________________________________________________
#
#       Enum Meta
#_____________________________________________________________________________

class AbcEnumMeta(_enum.EnumMeta, type[EnT2]):
    'General-purpose base Metaclass for all Enum classes.'

    #******  Class Instance Variables

    seq     : Sequence[EnT2]
    _lookup : EnumLookup[EnT2]

    _member_names_ : Sequence[str]
    _member_map_   : Mapping[str, EnT2]


    #******  Class Creation

    @classmethod
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw):
        ns: EnumDictType = super().__prepare__(clsname, bases)
        return ns

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: EnumDictType, /, *,
        skipflags = False, noidxbuild = False, **kw
    ):

        # Run generic Abc init hooks.
        abcm.nsinit(ns, bases, skipflags = skipflags)

        forbid = ENUM_RESERVE_NAMES.intersection(ns)
        if forbid:
            raise TypeError('Restricted names: %s' % ', '.join(forbid))

        # Create class.
        Class = super().__new__(cls, clsname, bases, ns, **kw)

        # Run generic Abc after hooks.
        abcm.clsafter(Class, ns, skipflags = skipflags)

        # Freeze Enum class attributes.
        Class._member_map_ = MapProxy(Class._member_map_)
        Class._member_names_ = tuple(Class._member_names_)

        if not len(Class):
            # No members to process.
            Class._after_init()
            return Class

        # Store the fixed member sequence.
        Class.seq = tuple(map(Class._member_map_.__getitem__, Class._member_names_))
        # Performance tweaks.
        enbm.fix_name_value(Class)
        # Init hook to process members before index is created.
        Class._on_init(Class)
        # Create index.
        Class._lookup = EnumLookup(Class) # type: ignore
        if not noidxbuild:
            Class._lookup.build()
        # After init hook.
        Class._after_init()
        # Cleanup.
        deleter = type(cls).__delattr__
        for hname in filter(Class.__dict__.__contains__, ENUM_CLEAN_METHODS):
            deleter(Class, hname)

        return Class

    #******  Subclass Init Hooks

    def _member_keys(cls, member: AbcEnum,/) -> Set[Hashable]:
        'Init hook to get the index lookup keys for a member.'
        return _EMPTY_SET

    def _on_init(cls, subcls: type[EnT]|AbcEnumMeta,/):
        '''Init hook after all members have been initialized, before index
        is created. **NB:** Skips abstract classes.'''
        pass

    def _after_init(cls):
        'Init hook once the class is initialized. Includes abstract classes.'
        pass

    #******  Class Call

    def __call__(cls: type[EnT]|AbcEnumMeta[EnT2], value: Any, names = None, **kw) -> EnT:
        if names is not None:
            return super().__call__(value, names, **kw)
        try:
            return cls._lookup[value].member
        except KeyError:
            pass
        member = cls.__new__(cls, value) # type: ignore
        return cls._lookup.pseudo(member)

    #******  Mapping(ish) Behavior

    def get(cls: type[EnT]|AbcEnumMeta[EnT2], key: Any, default: Any = _NOARG, /) -> EnT|EnT2:
        '''Get a member by an indexed reference key. Raises KeyError if not
        found and no default specified.'''
        try:
            return cls._lookup[key].member
        except KeyError:
            if default is _NOARG:
                raise
            return default

    def __getitem__(cls: type[EnT]|AbcEnumMeta[EnT2], key: Any, /) -> EnT|EnT2:
        return cls._lookup[key].member

    def __contains__(cls, key: Any, /):
        return key in cls._lookup

    #******  Sequence(ish) Behavior

    def __iter__(cls: type[EnT]|AbcEnumMeta[EnT2]) -> Iterator[EnT|EnT2]:
        return iter(cls.seq)

    def __reversed__(cls: type[EnT]|AbcEnumMeta[EnT2]) -> Iterator[EnT|EnT2]:
        return reversed(cls.seq)

    #******  Misc

    def __getattr__(cls, name, /):
        raise AttributeError(name)

    def __dir__(cls):
        return cls._member_names_

    @property
    def __members__(cls):
        # Override to not double-proxy
        return cls._member_map_

    @property
    @overload
    def seq(self: type[EnT]) -> Sequence[EnT]: ...
    del(seq)

class EnumLookup(Mapping[Any, EnumEntry[EnT]],
    metaclass = AbcMeta, skiphooks = True, skipflags = True
):
    'Enum entry lookup index.'

    __slots__ = (
        '__len__', '__getitem__', '__iter__', '__reversed__', 'build', 'pseudo'
    )

    def __init__(self, Owner: type[EnT], /):

        if hasattr(self, 'build'):
            raise TypeError

        keyfuncs = (self._default_keys, Owner._member_keys)
        source = {}

        ga = object.__getattribute__
        sa = object.__setattr__

        for name in filter(_isdund, self.__slots__):
            sa(self, name, ga(source, name))

        def pseudo(member):
            keys, entry = self._check_pseudo(member, Owner)
            for key in keys:
                source[key] = entry
            return entry.member

        def build():
            builder = self._makemap(Owner, keyfuncs)
            source.clear()
            source.update(builder)
            return self

        sa(self, 'build',  build)
        sa(self, 'pseudo', pseudo)

    @overload
    def build(self):...# type: ignore

    @overload
    def pseudo(self, member: EnT, /) -> EnT:...# type: ignore

    @classmethod
    def _makemap(cls, Owner: type[AbcEnum], keyfuncs: Collection[EnKeyFunc], /):
        members = Owner.seq
        pseudos = set(Owner._value2member_map_.values()) - set(members)
        builder = cls._seqmap(members, keyfuncs)
        if len(pseudos):
            builder |= cls._pseudomap(pseudos)
        return builder

    @classmethod
    def _seqmap(cls, members: Collection[AbcEnum], keyfuncs: Collection[EnKeyFunc], /):
        return {
            key : entry
            for member_keys, entry in zip(
                ({key for func in keyfuncs for key in func(member)}
                    for member in members
                ),
                (EnumEntry(member, i, nxt) for (i, member), nxt in zip(
                    enumerate(members), chain(members[1:], [None]))
                )
            ) for key in member_keys
        }

    @classmethod
    def _pseudomap(cls, pseudos: Collection[AbcEnum], /):
        return {key: entry
            for pseudo_keys, entry in (
                (cls._pseudo_keys(pseudo), EnumEntry(pseudo, None, None))
                for pseudo in pseudos
            ) for key in pseudo_keys
        }

    @classmethod
    def _check_pseudo(cls, pseudo: AbcEnum, ecls: type[AbcEnum], /):
        check = ecls._value2member_map_[pseudo.value]
        if check is not pseudo:
            from errors import Emsg
            raise TypeError from Emsg.ValueConflict(pseudo, check)
        if pseudo.name is not None:
            from errors import Emsg
            raise TypeError from Emsg.WrongValue(pseudo.name, None)
        return cls._pseudo_keys(pseudo), EnumEntry(pseudo, None, None)

    @classmethod
    def _pseudo_keys(cls, pseudo: AbcEnum, /) -> set[Hashable]:
        'Pseudo member lookup keys'
        return {pseudo, pseudo.value}

    @staticmethod
    def _default_keys(member: AbcEnum, /) -> set[Hashable]:
        'Default member lookup keys'
        return {member.name, (member.name,), member, member.value}

    def __setattr__(self, name, value, /):
        from errors import Emsg
        raise Emsg.ReadOnlyAttr(name, self)

    def __delattr__(self, name, /):
        from errors import Emsg
        raise Emsg.ReadOnlyAttr(name, self)

    def __repr__(self):
        return repr(dict(self))

    del(build, pseudo)

@static
class enbm:
    'Static Enum meta utils.'

    @staticmethod
    def fix_name_value(Class: type[EnT]|AbcEnumMeta[EnT2], /):

        # cache attribute for flag enum.
        if callable(getattr(Class, '__invert__', None)):
            Class._invert_ = None # type: ignore

        # Clear DynCa from class layout
        Class.name  = None # type: ignore
        Class.value = None # type: ignore

        # Assign name & value directly.
        for member in Class.seq:
            member.name = member._name_
            member.value = member._value_

#=============================================================================
#_____________________________________________________________________________
#
#       Enum Base Classes
#_____________________________________________________________________________

class AbcEnum(_enum.Enum, metaclass = AbcEnumMeta, skipflags = True):

    __slots__ = _EMPTY_SET

    name  : str
    value : Any

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    @classmethod
    def _on_init(cls: AbcEnumMeta, subcls: type[AbcEnum]):
        'Propagate hook up to metaclass.'
        type(cls)._on_init(cls, subcls)

    @classmethod
    def _member_keys(cls: AbcEnumMeta, member: AbcEnum):
        'Propagate hook up to metaclass.'
        return type(cls)._member_keys(cls, member)

    @classmethod
    def _after_init(cls: AbcEnumMeta):
        'Propagate hook up to metaclass.'
        type(cls)._after_init(cls)

    def __repr__(self):
        name = type(self).__name__
        try: return '<%s.%s>' % (name, self._name_)
        except AttributeError: return '<%s ?ERR?>' % name

class FlagEnum(_enum.Flag, AbcEnum, skipflags = True):

    name  : str|None
    value : int

    _invert_   : tuple[int, FlagEnum]

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

class abcf(FlagEnum, skipflags = True):
    'Enum flag for AbcMeta functionality.'

    # _invert_   : tuple[int, abcf]

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
    def read(cls, obj, default: abcf|int = 0, /, *, attr = ABC_FLAG_ATTR) -> abcf:
        "Get the flag (or `blank`) for any obj."
        return getattr(obj, attr, cls(default))

    @classmethod
    def save(cls, obj: F, value: abcf|int, /, *, attr = ABC_FLAG_ATTR) -> F:
        'Write the value, returns obj for decorator use.'
        setattr(obj, attr, cls(value))
        return obj

class IntEnum(int, AbcEnum):
    __slots__ = _EMPTY_SET
    # NB: "nonempty __slots__ not supported for subtype of 'IntEnum'"
    pass

class IntFlag(int, FlagEnum):
    __slots__ = _EMPTY_SET
    # NB: slots must be empty for int (layout conflict)
    pass

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Base Classes
#_____________________________________________________________________________

class Abc(metaclass = AbcMeta, skiphooks = True):
    'Convenience for using AbcMeta as metaclass.'

    __slots__ = _EMPTY_SET

class Copyable(Abc, skiphooks = True):

    __slots__ = _EMPTY_SET

    @abstract
    def copy(self: Self) -> Self:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return abcm.check_mrodict(subcls.mro(), '__copy__', 'copy')

#=============================================================================
#_____________________________________________________________________________

if 'Cleanup' or True:
    del(
        _abc,
        _enum,
        _EnumEntry,
        TypeVar,
        ParamSpec,
    )
    # fail if deleted
    final
    eauto