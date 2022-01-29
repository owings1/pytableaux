# Allowed local imports:
#
#  - errors
#  - tools.misc
from __future__ import annotations

__all__ = 'AbcMeta', 'AbcEnumMeta', 'AbcEnum', 'abcm', 'Abc', 'Copyable', 'abcf',

from errors import (
    instcheck as _instcheck
)

from collections.abc import Set as _Set
from types import (
    DynamicClassAttribute as DynClsAttr,
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
from functools import (
    partial,
    reduce,
)
from itertools import (
    chain,
    islice,
    starmap,
    zip_longest,
)
import operator as opr

# Bases (deletable)
import abc as _abc
import enum as _enum

_EMPTY = ()
_EMPTY_SET = frozenset()
_NOARG = object()
_NOGET = object()
_ABCF_ATTR = '_abc_flag'


def _thru(obj: T): return obj

class MapProxy:
    def __new__(cls, mapping:Mapping[KT, VT]):
        if isinstance(mapping, _MapProxy):
            return mapping
        return _MapProxy(mapping)

# Global decorators. Re-exported by decorators module.

@overload
def abstract(func: F) -> F: ...

abstract = _abc.abstractmethod

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

    abcf.static(cls)
    d = cls.__dict__

    for name, member in d.items():
        if not callable(member) or isinstance(member, type):
            continue
        setattr(cls, name, staticmethod(member))

    if '__new__' not in d:
        if '__call__' in d:
            # If the class directly defines a __call__ method,
            # use it for __new__.
            def fnew(cls, *args, **kw):
                return cls.__call__(*args, **kw)
        else:
            def fnew(cls): return cls
        cls.__new__ = fnew

    if '__init__' not in d:
        def finit(self): raise TypeError
        cls.__init__ = finit

    return cls

@_enum.unique
class abcf(_enum.Flag):
    'Enum flag for AbcMeta functionality.'

    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32

    _cleanable = before | temp | after
    # _protectable = immut | protect | locked

    def __call__(self, obj: F) -> F:
        "Add the flag to obj's meta flag. Return obj."
        return self.set(obj, self | self.get(obj))

    @classmethod
    def get(cls, obj, default: abcf|int = blank, /) -> abcf:
        return getattr(obj, _ABCF_ATTR, cls(default))

    @classmethod
    def set(cls, obj: F, value: abcf, /) -> F:
        setattr(obj, _ABCF_ATTR, cls(value))
        return obj

@static
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
        if slots and isinstance(slots, Iterable) and not isinstance(slots, _Set):
            ns['__slots__'] = frozenset(slots)

    def clsafter(Class: type, ns: Mapping, bases, /, deleter = type.__delattr__):
        abcf.blank(Class)
        for name, member in ns.items():
            mf = abcf.get(member)
            if mf is not mf.blank and mf in mf._cleanable:
                if mf.after in mf:
                    member(Class)
                deleter(Class, name)
        abcm.merge_mroattr(Class, '_lazymap_', {}, transform = MapProxy, rev = False)

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
        value = abcm.merged_mroattr(subcls, name, *args, transform= transform, **kw)
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

    def lazy_getattr(obj, name, /, setter = object.__setattr__):
        try:
            getter = type(obj)._lazymap_[name]
        except AttributeError:
            raise TypeError
        except KeyError:
            raise AttributeError(name) from None
        value = getter(obj)
        setter(obj, name, value)
        return value

class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname, bases, ns: dict, /, **kw):
        abcm.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        abcm.clsafter(Class, ns, bases, **kw)
        return Class


class EnumDictType(_enum._EnumDict):
    'Stub type for annotation reference.'
    _member_names: list[str]
    _last_values : list[Any]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str


class EnumEntry(NamedTuple):
    member : AbcEnum
    index  : int
    nextmember: AbcEnum | None

class AbcEnumMeta(_enum.EnumMeta):
    'General-purpose base Metaclass for all Enum classes.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    _lookup : MapProxy[Any, EnumEntry]
    _seq    : tuple[AbcEnum, ...]

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Creation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __new__(cls, clsname, bases, ns, /, flag = abcf.blank, **kw):

        # Run namespace init hooks.
        abcm.nsinit(ns, bases, flag = flag, **kw)
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

        # Store the fixed member sequence.
        Class._seq = tuple(map(Class._member_map_.get, Class.names))
        # Init hook to process members before index is created.
        Class._on_init(Class)
        # Create index.
        Class._lookup = cls._create_index(Class)
        # After init hook.
        Class._after_init()
        # Cleanup.
        cls._clear_hooks(Class)

        return Class

    @classmethod
    @final
    def _create_index(cls, Class: type[EnT]) -> Mapping[Any, EnumEntry]:
        'Create the member lookup index'
        # Member to key set functions.
        keys_funcs = cls._default_keys, Class._member_keys
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

    @staticmethod
    @final
    def _default_keys(member: EnT) -> Set[Hashable]:
        'Default member lookup keys'
        return set((
            member._name_, (member._name_,), member,
            member._value_, # hash(member),
        ))

    @classmethod
    @final
    def _clear_hooks(cls, Class: type):
        'Cleanup spent hook methods.'
        for _ in map(
            partial(type(cls).__delattr__, Class),
            cls._hooks & set(Class.__dict__)
        ): pass

    _hooks = frozenset((
        '_member_keys', '_on_init', '_after_init'
    ))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Subclass Init Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def _member_keys(cls, member: EnT) -> Set[Hashable]:
        'Init hook to get the index lookup keys for a member.'
        return _EMPTY_SET

    def _on_init(cls, Class: type[EnT]):
        '''Init hook after all members have been initialized, before index
        is created. Skips abstract classes.'''
        pass

    def _after_init(cls):
        'Init hook once the class is initialized. Includes abstract classes.'
        pass

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Container Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __contains__(cls, key):
        return cls.get(key, _NOGET) is not _NOGET

    def __getitem__(cls: type[EnT], key) -> EnT:
        if type(key) is cls: return key
        try: return cls._lookup[key][0]
        except (AttributeError, KeyError): pass
        return super().__getitem__(key)

    def __getattr__(cls, name):
        if name == 'index':
            # Allow DynClsAttr for member.index.
            try: return cls.indexof
            except AttributeError: pass
        return super().__getattr__(name)

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
        return list(cls.names)

    @property
    def __members__(cls: type[EnT]) -> dict[str, EnT]:
        # Override to not double-proxy
        return cls._member_map_

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Member Methods ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @DynClsAttr
    def names(cls):
        'The member names.'
        return cls._member_names_

    @DynClsAttr
    def seq(cls: type[EnT]) -> Sequence[EnT]:
        'The sequence of member objects.'
        try: return cls._seq
        except AttributeError: return ()

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
            except AttributeError:
                return cls.seq.index(cls[member])
        except KeyError:
            raise ValueError(member)

    index = indexof

    def entryof(cls, key) -> EnumEntry:
        try:
            return cls._lookup[key]
        except KeyError:
            return cls._lookup[cls[key]]
        except AttributeError:
            raise KeyError(key)

class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'
    __slots__ = _EMPTY
    # __getattr__ = abcm.lazy_getattr

class AbcEnum(_enum.Enum, metaclass = AbcEnumMeta):

    __slots__ = _EMPTY

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Meta Class Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
        try: return '<%s.%s>' % (name, self.name)
        except AttributeError: return '<%s ?ERR?>' % name

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

# Type vars
T  = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')
KT = TypeVar('KT')
VT = TypeVar('VT')
RT = TypeVar('RT')
Self = TypeVar('Self')

T_co = TypeVar('T_co', covariant = True)
T_contra = TypeVar('T_contra', contravariant = True)

F   = TypeVar('F', bound = Callable[..., Any])
TT  = TypeVar('TT', bound = type)
EnT = TypeVar('EnT', bound = AbcEnum)

P = ParamSpec('P')

del(_abc, _enum, TypeVar, ParamSpec)