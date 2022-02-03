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

from collections import defaultdict
from collections.abc import Set
from functools import (
    reduce,
)
from itertools import (
    chain,
    islice,
    repeat,
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

    ns = cls.__dict__

    for name, member in ns.items():
        if not isinstance(member, FunctionType):
            continue
        setattr(cls, name, staticmethod(member))

    if '__new__' not in ns:
        cls.__new__ = _thru

    if '__init__' not in ns:
        def finit(self): raise TypeError
        cls.__init__ = finit

    return cls


@static
class abcm:
    '''Static meta util functions.'''

    def nsinit(ns: dict, bases, /, **kw):
        # iterate over copy since hooks may modify ns.
        for member in tuple(ns.values()):
            mf = abcf.read(member)
            if mf.before in mf:
                member(ns, bases, **kw)
        # cast slots to a set
        slots = ns.get('__slots__')
        if isinstance(slots, Iterable) and not isinstance(slots, Set):
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
            mf = abcf.read(member)
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
        # this is called infrequently
        from typing import get_type_hints, get_args, get_origin
        annot = get_type_hints(obj, include_extras = True)
        return {
            k: get_args(v) for k,v in annot.items()
            if get_origin(v) is Annotated
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
        'Decorator factory for specifying available hooks.'
        def decorator(func: F): return HookInfo.funcupdate(func, names)
        return decorator

    def hookinfo(Class: type):
        return HookInfo(Class)

    def copyfunc(f: FunctionType|F) -> FunctionType|F:
        'Copy a function.'
        func = FunctionType(
            f.__code__,
            f.__globals__,
            f.__name__,
            f.__defaults__,
            f.__closure__,
        )
        if f.__kwdefaults__ is not None:
            func.__kwdefaults__ = dict(f.__kwdefaults__)
        return func

class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname, bases, ns: dict, /, hooks = None, **kw):

        abcm.nsinit(ns, bases, **kw)

        Class = super().__new__(cls, clsname, bases, ns, **kw)

        try:
            HookInfo.buildimpl(Class, hooks)
        except NameError:
            if clsname != 'HookInfo': raise

        abcm.clsafter(Class, ns, bases, **kw)

        try:
            HookInfo.buildinfo(Class)
        except NameError:
            if clsname != 'HookInfo': raise

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
            return HookInfo.addimpl(cls, func, names)
        return decorator


@static
class enbm:
    'Static enum meta utils.'

    def build_index(Class: type[EnT]) -> Mapping[Any, tuple[EnT, int, EnT|None]]:
        'Create the member lookup index'
        # Member to key set functions.
        keys_funcs = enbm.default_keys, Class._member_keys
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

    def default_keys(member: EnT) -> Set[Hashable]:
        'Default member lookup keys'
        return set((
            member._name_, (member._name_,), member,
            member._value_, # hash(member),
        ))

    def fix_name_value(Class: type[EnT]):

        # cache attribute for flag enum.
        Class._invert_ = None

        # Clear DynCa from class layout
        Class.name  = None
        Class.value = None

        # Assign name & value directly.
        for member in Class.seq:
            member.name = member._name_
            member.value = member._value_

class AbcEnumMeta(_enum.EnumMeta):
    'General-purpose base Metaclass for all Enum classes.'

    # * * * * * * *  Class Instance Variables  * * * * * * * * * #

    seq     : tuple[EnT, ...]
    _lookup : MapProxy[Any, EnumEntry]
    _member_names_: tuple[str, ...]

    # * * * * * * *  Class Creation  * * * * * * * * * #

    def __new__(cls, clsname, bases, ns, /, **kw):

        # Run namespace init hooks.
        try:
            abcm.nsinit(ns, bases, **kw)
        except NameError:
            if clsname != 'abcf': raise
            skipafter = True
        else:
            skipafter = False
            
        forbid = _ENUM_RESTRICTNAMES.intersection(ns)
        if forbid:
            raise TypeError('Restricted names: %s' % ', '.join(forbid))

        # Create class.
        Class = super().__new__(cls, clsname, bases, ns, **kw)

        # Run after hooks.
        skipafter or abcm.clsafter(Class, ns, bases, **kw)

        # Freeze Enum class attributes.
        Class._member_map_ = MapProxy(Class._member_map_)
        Class._member_names_ = tuple(Class._member_names_)

        if not len(Class):
            # No members to process.
            Class._after_init()
            return Class

        # Store the fixed member sequence.
        Class.seq = tuple(map(Class._member_map_.get, Class._member_names_))
        # Performance tweaks.
        enbm.fix_name_value(Class)
        # Init hook to process members before index is created.
        Class._on_init(Class)
        # Create index.
        Class._lookup = enbm.build_index(Class)
        # After init hook.
        Class._after_init()
        # Cleanup.
        deleter = type(cls).__delattr__
        for hname in filter(Class.__dict__.__contains__, _ENUM_HOOKMETHODS):
            deleter(Class, hname)

        return Class

    # * * * * * * *  Subclass Init Hooks  * * * * * * * * * #

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

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

# Enum utils

class EnumEntry(NamedTuple):
    member : AbcEnum
    index  : int
    nextmember: AbcEnum | None

class abcf(_enum.Flag, metaclass = AbcEnumMeta):
    'Enum flag for AbcMeta functionality.'
    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32

    _cleanable = before | temp | after

    def __call__(self, obj: F) -> F:
        "Add the flag to obj's meta flag. Return obj."
        return self.save(obj, self | self.read(obj))

    @classmethod
    def read(cls, obj, default: abcf|int = 0,
    /, *, _attr = _ABCF_ATTR) -> abcf:
        return getattr(obj, _attr, cls(default))

    @classmethod
    def save(cls, obj: F, value: abcf|int, /, *, _attr = _ABCF_ATTR) -> F:
        setattr(obj, _attr, cls(value))
        return obj

    from tools.patch import _enum_flag_invert as __invert__


@final
class HookInfo(Mapping[str, tuple[str, ...]], metaclass = AbcMeta):

    __slots__ = 'cls', 'mapping'

    def __init__(self, Class: type):
        self.cls = Class
        try:
            self.mapping = ABC_HOOKINFO[Class]
        except KeyError:
            raise TypeError("No hooks defined for class '%s'" % Class)

    def hooks(self):
        'Hook names ( hook, ... ).'
        return tuple(self)

    def names(self):
        'Flat sequence of class member names ( name, ... )'
        return tuple(sorted(
            name for names in self.values() for name in names
        ))

    def pairs(self):
        'Hook, name pairs( (hook, name), ... )'
        return tuple(
            item for items in (
                zip(repeat(hook), names)
                for hook, names in self.items()
            )
            for item in items
        )

    @overload
    def attrs(self) -> dict[str, tuple[tuple[str, FunctionType], ...]]: ...

    @overload
    def attrs(self, hook: str) -> tuple[tuple[str, FunctionType], ...]: ...

    def attrs(self, hook = None):
        '''
        With hook argument:
            ( (name, member), ... )
        Without argument, all hooks:
            { hook: ( (name, member), ... ) }'''
        Class = self.cls
        it = self if hook is None else (hook,) 
        m = {
            key: tuple(
                (name, getattr(Class, name))
                for name in self[key]
            )
            for key in it
        }
        return m if hook is None else m[hook]

    def __repr__(self):
        return 'HookInfo[%s]=%s' % (self.cls.__name__, repr(dict(self)))

    @abcf.after
    def opers(cls: type[HookInfo], *_):

        from collections import defaultdict
        from functools import wraps
        import operator as opr

        def compress(items, defaultdict = defaultdict):
            build: dict[str, list] = defaultdict(list)
            for hook, name in items:
                build[hook].append(name)
            return {key: tuple(values) for key, values in build.items()}

        for opername in ('__sub__', '__and__', '__or__', '__xor__'):

            oper = getattr(opr, opername)

            @wraps(oper)
            def f(self, other:HookInfo|type, /, *,
                cls = cls, pairs = cls.pairs, oper = oper, compress = compress
            ):
                if not isinstance(other, cls):
                    try:
                        other = cls(other)
                        other.mapping
                    except:
                        return NotImplemented
                return compress(sorted(
                    oper(
                        set(pairs(self)),
                        set(pairs(other))
                    )
                ))

            f.__name__ = f.__qualname__ = opername
            setattr(cls, opername, f)

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, key):
        return self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __reversed__(self):
        return reversed(self.mapping)

    @static
    def addimpl(cls, func: F, names, /, *, attr = _ABCHOOK_IMPL_ATTR):
        try:
            value = getattr(func, attr)
        except AttributeError:
            value = dict()
            setattr(func, attr, value)
        impl = value.setdefault(cls, {})
        for name in names:
            if name in impl:
                raise TypeError from Emsg.DuplicateKey(name)
            impl[name] = func
        return func

    @static
    def buildimpl(Class: TT, hooks: dict[type, dict[str, Callable]] = None,
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
            clsinfo = HookInfo(cls)

            for hook, member in impl.items():
                if hook not in clsinfo:
                    raise TypeError from Emsg.MissingKey(hook)

                for method, func in clsinfo.attrs(hook):
                    # Check the existing kwdefault value.
                    defval = func.__kwdefaults__[hook]
                    if defval is not None:
                        if defval is member: continue
                        # Protection until the behavior is defined.
                        raise TypeError from Emsg.ValueConflictFor(hook, member, defval)
                    if method not in ns:
                        # Copy the function if it is not already in the Class dict.
                        func = abcm.copyfunc(func)
                        setattr(Class, method, func)
                    # Write the kwdefaults
                    func.__kwdefaults__[hook] = member
    @static
    def funcupdate(func: F, hooks: Iterable[str], /, *, attr = _ABCHOOK_INFO_ATTR):
        # Add hook names to the function's hookinfo attribute, initializing
        # with an empty set if necessary.
        value = getattr(func, attr, None)
        if value is None:
            value = set()
            setattr(func, attr, value)
        value.update(hooks)
        return func

    @overload
    @static
    def buildinfo(Class: TT):...

    @static
    @overload
    def all() -> Mapping[type, Mapping[str, tuple[str, ...]]]: ...

    @abcf.before
    def ini(ns: dict, *_):

        main = {}
        classes = {}
        proxy = MapProxy(main)

        def buildinfo(Class: TT, /, *, attr = _ABCHOOK_INFO_ATTR):

            ns = Class.__dict__
            if Class in classes:
                raise TypeError('HookInfo already configured for %s' % Class)

            builder: dict[str, set[str]] = defaultdict(set)

            for name, member in ns.items():

                hooks = getattr(member, attr, None)
                if not hooks:
                    continue
                if not isinstance(member, FunctionType):
                    raise Emsg.InstCheck(member, FunctionType)
                for hook in hooks:
                    builder[hook].add(name)

            if builder:
                hookinfo = dict(
                    (hook, tuple(sorted(builder[hook])))
                    for hook in sorted(builder)
                )
                classes[Class] = hookinfo
                main[Class] = MapProxy(hookinfo)

        ns.update(
            buildinfo = static(buildinfo),
            all = static(lambda: proxy)
        )

ABC_HOOKINFO = HookInfo.all()

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #
#
# Enum Base classes

class AbcEnum(_enum.Enum, metaclass = AbcEnumMeta):

    __slots__ = _EMPTY

    _invert_: tuple[int, FlagEnum] | None
    name: str
    value: Any

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


class FlagEnum(_enum.Flag, AbcEnum):
    __slots__ = '_value_', '_invert_', 'name', 'value'
    from tools.patch import _enum_flag_invert as __invert__

class IntEnum(_enum.IntEnum, AbcEnum):
    __slots__ = _EMPTY
    # NB: "nonempty __slots__ not supported for subtype of 'IntEnum'"
    pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #
#
#  Abc Base Class

class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'

    __slots__ = _EMPTY

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

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

del(
    _abc, _enum, TypeVar, ParamSpec,

)