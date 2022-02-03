# Allowed local imports:
#
#  - errors
#  - tools.misc
from __future__ import annotations

__all__ = (
    'AbcMeta',
    'AbcEnumMeta',
    'AbcEnum',
    'abcf',
    'abcm',
    'Abc',
    'Copyable',
    'final',
    'overload',
    'abstract',
    'static',
    'MapProxy',
)

from errors import (
    instcheck as _instcheck,
    Emsg,
)

from collections import deque
from collections.abc import (
    Set as _Set
)
from functools import (
    reduce,
)
from itertools import (
    chain,
    islice,
    starmap,
    zip_longest,
)
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
    Hashable,
    Iterable,
    Iterator,
    # Literal,
    Mapping,
    NamedTuple,
    Sequence,
    Set,
    SupportsIndex,

    # Util references
    get_type_hints as _get_type_hints,
    get_args       as _get_args,
    get_origin     as _get_origin,

    # deletable references
    ParamSpec,
    TypeVar,
)

# Bases (deletable)
import abc as _abc
import enum as _enum

ABC_HOOKINFO: Mapping[type, Mapping[str, frozenset[str]]]

_EMPTY = ()
_EMPTY_SET = frozenset()
_NOARG = object()
_NOGET = object()
_ABCF_ATTR    = '_abc_flag'
_ABCHOOK_IMPL_ATTR = '_abc_hook_impl'
_ABCHOOK_INFO_ATTR = '_abc_hook_info'
_ENUM_RESTRICTNAMES = frozenset(
    ('names', 'seq', '_lookup', 'index', 'indexof', 'get', 'entryof', '_invert_')
)
_ENUM_HOOKMETHODS = frozenset(
    ('_member_keys', '_on_init', '_after_init')
)

def _thru(obj: T): return obj

# Global decorators. Re-exported by decorators module.

from abc import abstractmethod as abstract

@overload
def static(cls: TT) -> TT: ...

@overload
def static(meth: Callable[..., T]) -> staticmethod[T]: ...

def static(cls):
    'Static class decorator wrapper around staticmethod'

    if not isinstance(cls, type):
        if isinstance(cls, (classmethod, staticmethod)):
            return cls
        _instcheck(cls, Callable)
        return staticmethod(cls)

    try:
        abcf.static(cls)
    except NameError:
        if cls is not abcm:
            raise
        pass
    ns = cls.__dict__

    for name, member in ns.items():
        if not callable(member) or isinstance(member, type):
            continue
        setattr(cls, name, staticmethod(member))

    if '__new__' not in ns:
        if '__call__' in ns:
            # If the class directly defines a __call__ method,
            # use it for __new__.
            def fnew(cls, *args, **kw):
                return cls.__call__(*args, **kw)
        else:
            def fnew(cls): return cls
        cls.__new__ = fnew

    if '__init__' not in ns:
        def finit(self): raise TypeError
        cls.__init__ = finit

    return cls


class abcm:
    '''Util functions. Can also be used by meta classes that
    cannot inherit from AbcMeta, like EnumMeta.'''

    def nsinit(ns: dict, bases, /, **kw):
        # iterate over copy since hooks may modify ns.
        for member in tuple(ns.values()):
            mf = abcf.get(member)
            if mf.before in mf:
                member(ns, bases, **kw)
        # cast slots to a set
        slots = ns.get('__slots__')
        if isinstance(slots, Iterable) and not isinstance(slots, _Set):
            ns['__slots__'] = frozenset(slots)

    def clsafter(Class: TT, ns: Mapping = None, bases = None, /,
        deleter = type.__delattr__, **kw):
        # Allow use as standalone class decorator
        if ns is None: ns = Class.__dict__.copy()
        if bases is None: bases = Class.__bases__
        abcf.blank(Class)
        todelete = set()
        nsitems = ns.items()
        for name, member in nsitems:
            # Finish calling the 'after' hooks before anything else, since
            # they might modify other meta config.
            mf = abcf.get(member)
            if mf is not mf.blank and mf in mf._cleanable:
                if mf.after in mf:
                    member(Class)
                todelete.add(name)
        for name in todelete:
            deleter(Class, name)
        return Class

    def isabstract(obj):
        if isinstance(obj, type):
            return bool(len(getattr(obj, '__abstractmethods__', _EMPTY)))
        return bool(getattr(obj, '__isabstractmethod__', False))

    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        annot = _get_type_hints(obj, include_extras = True)
        return {
            k: _get_args(v) for k,v in annot.items()
            if _get_origin(v) is Annotated
        }

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
        return True

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
            if initial is _NOARG:
                initial = default
            it = (getattr(c, name, default) for c in it)
        if initial is _NOARG:
            value = reduce(oper, it)
        else:
            value = reduce(oper, it, initial)
        return transform(value)

    def merge_mroattr(subcls: type, name: str,
        *args,
        transform: Callable[..., T] = _thru,
        **kw
    ) -> T:
        setter = kw.pop('setter', setattr)
        value = abcm.merged_mroattr(subcls, name, *args, transform = transform, **kw)
        setter(subcls, name, value)
        return value

    def mroiter(subcls: type[T], /,
        supcls: type|tuple[type, ...]|None = None,
        *,
        rev = True,
        start: SupportsIndex = 0
    ) -> Iterable[type[T]]:
        it = subcls.mro()
        if rev:
            it = reversed(it)
        else:
            it = iter(it)
        if supcls is not None:
            it = filter(lambda c: issubclass(c, supcls), it)
        if start != 0:
            it = islice(it, start)
        return it

    def hookable(*names: str):
        def decorator(func: F):
            return _hookinfo_decorate(func, names)
        return decorator

class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname, bases, ns: dict, /, hooks = None, **kw):
        abcm.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        _hookimpl_build(Class, hooks)
        abcm.clsafter(Class, ns, bases, **kw)
        _hookinfo_build(Class)
        return Class

    def hook(cls, *names: str):
        'Decorator factory for tagging hook implementation.'
        if not names:
            raise TypeError('Empty args.')
        avail = ABC_HOOKINFO.get(cls, _EMPTY_SET)
        for name in names:
            if name not in avail:
                raise TypeError('Invalid hook') from Emsg.MissingKey(name)
        def decorator(func: F):
            return _hookimpl_decorate(cls, func, names)
        return decorator

static(abcm)

class AbcEnumMeta(_enum.EnumMeta):
    'General-purpose base Metaclass for all Enum classes.'

    # * * * * * * *  Class Instance Variables  * * * * * * * * * #

    seq     : tuple[EnT, ...]
    _lookup : MapProxy[Any, EnumEntry]
    _member_names_: tuple[str, ...]

    # * * * * * * *  Class Creation  * * * * * * * * * #

    def __new__(cls, clsname, bases, ns, /, **kw):

        # Run namespace init hooks.
        abcm.nsinit(ns, bases, **kw)
        forbid = _ENUM_RESTRICTNAMES.intersection(ns)
        if forbid:
            raise TypeError('Restricted names: %s' % ', '.join(forbid))
        # Create class.
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        # Run after hooks.
        abcm.clsafter(Class, ns, bases, **kw)

        # Freeze Enum class attributes.
        Class._member_map_ = MapProxy(Class._member_map_)
        Class._member_names_ = tuple(Class._member_names_)

        if not len(Class):
            # No members to process.
            Class._after_init()
            return Class

        Class._invert_ = None

        # Store the fixed member sequence.
        Class.seq = tuple(map(Class._member_map_.get, Class._member_names_))
        # Init hook to process members before index is created.
        Class._on_init(Class)
        # Create index.
        Class._lookup = _enum_build_index(Class)
        # After init hook.
        Class._after_init()
        # Cleanup.
        deleter = type(cls).__delattr__
        for hname in filter(Class.__dict__.__contains__, _ENUM_HOOKMETHODS):
            deleter(Class, hname)

        return Class

    # * * * * * * *  Subclass Init Hooks  * * * * * * * * * #

    def _member_keys(cls, member: EnT) -> _Set[Hashable]:
        'Init hook to get the index lookup keys for a member.'
        return _EMPTY_SET

    def _on_init(cls, Class: type[EnT]):
        '''Init hook after all members have been initialized, before index
        is created. Skips abstract classes.'''
        pass

    def _after_init(cls):
        'Init hook once the class is initialized. Includes abstract classes.'
        pass

    # * * * * * * *  Container Behavior  * * * * * * * * * #

    def __contains__(cls, key):
        return cls.get(key, _NOGET) is not _NOGET

    def __getitem__(cls: type[EnT], key) -> EnT:
        if type(key) is cls: return key
        try: return cls._lookup[key][0]
        except (AttributeError, KeyError): pass
        return super().__getitem__(key)

    def __getattr__(cls, name):
        raise AttributeError(name)

        # print('AbcEnumMeta.__getattr__', name)

        # if name == 'index':
        #     # Allow DynClsAttr for member.index.
        #     try: return cls.indexof
        #     except AttributeError: pass
        # return super().__getattr__(name)

    def __iter__(cls: type[EnT]) -> Iterator[EnT]:
        return iter(cls.seq)

    def __reversed__(cls: type[EnT]) -> Iterator[EnT]:
        return reversed(cls.seq)

    def __call__(cls: type[EnT], value, *args) -> EnT:
        if not args:
            try: return cls[value]
            except KeyError: pass
        return super().__call__(value, *args)

    def __dir__(cls):
        return list(cls._member_names_)

    @property
    def __members__(cls: type[EnT]) -> dict[str, EnT]:
        # Override to not double-proxy
        return cls._member_map_

    # * * * * * * *  Member Methods  * * * * * * * * * #

    def get(cls: type[EnT], key, default = _NOARG) -> EnT:
        '''Get a member by an indexed reference key. Raises KeyError if not
        found and no default specified.'''
        try: return cls[key]
        except KeyError:
            if default is _NOARG: raise
            return default

    def indexof(cls: type[EnT], member: EnT) -> int:
        'Get the sequence index of the member. Raises ValueError if not found.'
        try:
            try:
                return cls._lookup[member][1]
            except KeyError:
                return cls._lookup[cls[member]][1]
        except KeyError:
            raise ValueError(member)

    def entryof(cls, key) -> EnumEntry:
        try:
            return cls._lookup[key]
        except KeyError:
            return cls._lookup[cls[key]]
        except AttributeError:
            raise KeyError(key)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

# Type vars

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

T_co  = TypeVar('T_co', covariant = True)
KT_co = TypeVar('KT_co', covariant = True)
VT_co = TypeVar('VT_co', covariant = True)
T_contra = TypeVar('T_contra', contravariant = True)

# Callable bound, use for decorator, etc.
F   = TypeVar('F',  bound = Callable[..., Any])
# Type bound, use for class decorator, etc.
TT  = TypeVar('TT', bound = type)

P = ParamSpec('P')

class EnumDictType(_enum._EnumDict):
    'Stub type for annotation reference.'
    _member_names: list[str]
    _last_values : list[Any]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

# Utils

class MapProxy(Mapping[KT, VT]):
    def __new__(cls, mapping:Mapping[KT, VT]|Iterable[tuple[KT, VT]] = None) -> _MapProxy[KT, VT]:
        if mapping is None:
            return _EMPTY_MAP
        if isinstance(mapping, _MapProxy):
            return mapping
        if not isinstance(mapping, Mapping):
            mapping = dict(mapping)
        return _MapProxy(mapping)

_EMPTY_MAP = MapProxy({})

def _hookimpl_decorate(cls, func: F, names, /, *, _attr = _ABCHOOK_IMPL_ATTR):
    try:
        hookimpl = getattr(func, _attr)
    except AttributeError:
        hookimpl = dict()
        setattr(func, _attr, hookimpl)
    impl = hookimpl.setdefault(cls, {})
    for name in names:
        if name in impl:
            raise TypeError from Emsg.DuplicateKey(name)
        impl[name] = func
    return func

def _hookinfo_decorate(func: F, names, /, *, _attr = _ABCHOOK_INFO_ATTR):
    try:
        hookinfo = getattr(func, _attr)
    except AttributeError:
        hookinfo = set()
        setattr(func, _attr, hookinfo)
    hookinfo.update(names)
    return func

def _hookinfo_build(Class: TT, /, *, _main = {}, _classes = {}):   
    attr = _ABCHOOK_INFO_ATTR
    ns = Class.__dict__
    clsinfo: dict[str, set[str]] = {}
    for name, member in ns.items():
        hooks = getattr(member, attr, _EMPTY_SET)
        if not hooks:
            continue
        if not isinstance(member, FunctionType):
            raise TypeError(
                "Unsupported hook member type '%s' for class '%s' ('%s')" %
                (type(member), Class, name)
            )
        for hook in hooks:
            if hook not in clsinfo:
                clsinfo[hook] = set()
            clsinfo[hook].add(name)
    if clsinfo:
        for hook, names in clsinfo.items():
            clsinfo[hook] = frozenset(names)
        _classes[Class] = clsinfo
        _main[Class] = MapProxy(clsinfo)

ABC_HOOKINFO = MapProxy(_hookinfo_build.__kwdefaults__['_main'])

def _hookimpl_build(Class: TT, hooks: dict[type, dict[str, Callable]] = None,
    /, *, _attr = _ABCHOOK_IMPL_ATTR):
    if hooks is None:
        hooks = {}
    else:
        hooks = {key: hooks[key].copy() for key in hooks}
    ns = Class.__dict__
    for member in ns.values():
        value: dict = getattr(member, _attr, None)
        if not value:
            continue
        for cls, impl in value.items():
            if cls not in hooks:
                hooks[cls] = {}
            for hook in impl:
                if hook in hooks[cls]:
                    raise TypeError from Emsg.DuplicateKey(hook)
                hooks[cls][hook] = member
    if not hooks:
        return
    for cls, impl in hooks.items():
        try:
            clsinfo = ABC_HOOKINFO[cls]
        except KeyError:
            raise TypeError("No hooks defined for class '%s'" % cls)
        for hook, member in impl.items():
            if hook not in clsinfo:
                raise TypeError from Emsg.MissingKey(hook)
            for method in clsinfo[hook]:
                func = getattr(Class, method)
                try:
                    defval = func.__kwdefaults__[hook]
                except (KeyError, TypeError):
                    raise TypeError("Cannot get kw default for '%s'" % method)
                if defval is not None:
                    if defval is member:
                        continue
                    raise TypeError from Emsg.ValueConflictFor(hook, member, defval)
                if method not in ns:
                    # Copy the function if it is not already in the Class dict.
                    func = _copyf(func)
                    setattr(Class, method, func)
                func.__kwdefaults__[hook] = member

def _copyf(f: FunctionType) -> FunctionType:
    func = FunctionType(
        f.__code__, f.__globals__, f.__name__,
        f.__defaults__, f.__closure__,
    )
    if f.__kwdefaults__:
        func.__kwdefaults__ = dict(f.__kwdefaults__)
    return func

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

# Enum utils

class EnumEntry(NamedTuple):
    member : AbcEnum
    index  : int
    nextmember: AbcEnum | None

def _enum_default_keys(member: EnT) -> Set[Hashable]:
    'Default member lookup keys'
    return set((
        member._name_, (member._name_,), member,
        member._value_, # hash(member),
    ))

def _enum_build_index(Class: type[EnT]) -> Mapping[Any, tuple[EnT, int, EnT|None]]:
    'Create the member lookup index'
    # Member to key set functions.
    keys_funcs = _enum_default_keys, Class._member_keys
    # Merges keys per member from all key_funcs.
    keys_it = map(set, map(
        chain.from_iterable, zip(*(
            map(f, Class) for f in keys_funcs
        ))
    ))
    # Builds the member cache entry: (member, i, next-member).
    value_it = starmap(EnumEntry, zip_longest(
        Class, range(len(Class)), Class.seq[1:]
    ))
    # Fill in the member entries for all keys and merge the dict.
    return MapProxy(reduce(opr.or_,
        starmap(dict.fromkeys, zip(keys_it, value_it))
    ))

def _enum_flag_invert(self: FlagEnum):
    # copied and adapted from
    #   - core enum module, and
    #   - https://github.com/python/cpython/blob/a668e2a1b863f2d/Lib/enum.py
    cached = self._invert_
    value = self._value_
    if cached is not None:
        if cached[0] == value:
            return cached[1]
        self._invert_ = None
    cls = type(self)
    members, uncovered = _enum_flag_decompose(cls, value)
    inverted = cls(0)
    for m in cls:
        if m not in members and not (m._value_ & value):
            inverted = inverted | m
    result = cls(inverted)
    self._invert_ = value, result
    result._invert_ = result._value_, self
    return result

def _enum_flag_decompose(flag: type[FlagEnum], value: int):
    # copied and adapted from
    #   - core enum module, and
    #   - https://github.com/python/cpython/blob/a668e2a1b863f2d/Lib/enum.py
    # _decompose is only called if the value is not named
    not_covered = value
    negative = value < 0
    members: list[FlagEnum] = []
    for member in flag:
        member_value = member._value_
        if member_value and member_value & value == member_value:
            members.append(member)
            not_covered &= ~member_value
    if not negative:
        tmp = not_covered
        while tmp:
            flag_value = 2 ** tmp.bit_length() - 1
            if flag_value in flag._value2member_map_:
                members.append(flag._value2member_map_[flag_value])
                not_covered &= ~flag_value
            tmp &= ~flag_value
    if not members and value in flag._value2member_map_:
        members.append(flag._value2member_map_[value])
    members.sort(key = lambda m: m._value_, reverse = True)
    if len(members) > 1 and members[0]._value_ == value:
        # we have the breakdown, don't need the value member itself
        members.pop(0)
    return members, not_covered

# :-)
_enum._decompose = _enum_flag_decompose

# @_enum.unique
class abcf(_enum.Flag):
    'Enum flag for AbcMeta functionality.'
    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32

    _cleanable = before | temp | after

    def __call__(self, obj: F) -> F:
        "Add the flag to obj's meta flag. Return obj."
        return self.set(obj, self | self.get(obj))

    @classmethod
    def get(cls, obj, default: abcf|int = 0,
    /, *, _attr = _ABCF_ATTR) -> abcf:
        return getattr(obj, _attr, cls(default))

    @classmethod
    def set(cls, obj: F, value: abcf|int, /, *, _attr = _ABCF_ATTR) -> F:
        setattr(obj, _attr, cls(value))
        return obj

    __invert__ = _enum_flag_invert

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

# Base classes


class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'
    __slots__ = _EMPTY

class AbcEnum(_enum.Enum, metaclass = AbcEnumMeta):

    __slots__ = _EMPTY

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    # Propagate class hooks up to metaclass, so they can be implemented
    # in either the meta or concrete classes.

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

EnT = TypeVar('EnT', bound = AbcEnum)

###### copied from enum module and adjusted attr names for performance.

class FlagEnum(_enum.Flag, AbcEnum):
    __slots__ = _EMPTY
    __invert__ = _enum_flag_invert
    _invert_: tuple[int, FlagEnum] | None

class IntEnum(_enum.IntEnum, AbcEnum):
    pass
######

class Copyable(Abc):

    __slots__ = _EMPTY

    @abstract
    def copy(self: T) -> T:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return abcm.check_mrodict(subcls.mro(), '__copy__', 'copy', '__deepcopy__')

del(_abc, _enum, TypeVar, ParamSpec)