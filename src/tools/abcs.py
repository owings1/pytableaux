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
    DynamicClassAttribute as DynCa,
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
    ParamSpec,
    TypeVar,
)

# Bases (deletable)
import abc as _abc
import enum as _enum

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

if True:
    # Type Vars

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

_EMPTY = ()
_EMPTY_SET = frozenset()
_NOARG = object()
_NOGET = object()

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

ABC_FLAG_ATTR     = '_abc_flag'
ABC_HOOKIMPL_ATTR = '_abc_hook_impl'
ABC_HOOKINFO_ATTR = '_abc_hook_info'

ABC_HOOKINFO: Mapping[type, Mapping[str, frozenset[str]]]

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

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

class MapProxy(Mapping[KT, VT]):
    'Cast to a proxy if not already.'

    EMPTY_MAP = _MapProxy({})

    def __new__(cls,
        mapping: Mapping[KT, VT] | Iterable[tuple[KT, VT]] = None
    ) -> _MapProxy[KT, VT]:

        if mapping is None: return cls.EMPTY_MAP

        if isinstance(mapping, _MapProxy):
            return mapping

        if not isinstance(mapping, Mapping):
            mapping = dict(mapping)

        return _MapProxy(mapping)
    
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

@static
class abcm:
    '''Static meta util functions.'''

    def nsinit(ns: dict, bases, /, **kw):
        'Class namespace prepare routine.'
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
        'After class init routine.'
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
        # This is called infrequently, so we import lazily.
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
        *, rev = True, start: SupportsIndex = 0
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

    def hookable(*hooks: str, attr = ABC_HOOKINFO_ATTR):
        'Decorator factory for specifying available hooks.'
        def decorator(func: F):
            value = getattr(func, attr, None)
            if value is None:
                value = set()
                setattr(func, attr, value)
            value.update(hooks)
            return func
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
            HookInfo.init_implcls(Class, hooks)
        except NameError:
            # Not initialized.
            if clsname != 'HookInfo': raise

        abcm.clsafter(Class, ns, bases, **kw)

        try:
            HookInfo.init_provider(Class)
        except NameError:
            if clsname != 'HookInfo': raise

        return Class

    def hook(cls, *hooks: str, attr = ABC_HOOKIMPL_ATTR):
        'Decorator factory for tagging hook implementation.'
        def decorator(func: F):
            value = getattr(func, attr, None)
            if value is None:
                value = dict()
                setattr(func, attr, value)
            impl = value.setdefault(cls, {})
            for name in hooks:
                if name in impl:
                    raise TypeError from Emsg.DuplicateKey(name)
                impl[name] = func
            return func
        return decorator

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #


ENUM_RESERVE_NAMES = frozenset(
    ('names', 'seq', '_lookup', 'index', 'indexof',
    'get', 'entryof', '_invert_')
)
ENUM_HOOK_METHODS = frozenset(
    ('_member_keys', '_on_init', '_after_init')
)


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


class EnumEntry(NamedTuple):
    member : AbcEnum
    index  : int
    nextmember: AbcEnum | None

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
            skipafter = False
            abcm.nsinit(ns, bases, **kw)
        except NameError:
            if clsname != 'abcf': raise
            skipafter = True

        forbid = ENUM_RESERVE_NAMES.intersection(ns)
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
        for hname in filter(Class.__dict__.__contains__, ENUM_HOOK_METHODS):
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
        if type(key) is cls:
            return key
        try:
            return cls._lookup[key][0]
        except (AttributeError, KeyError):
            pass
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

    @property
    def __members__(cls: type[EnT]) -> dict[str, EnT]:
        # Override to not double-proxy
        return cls._member_map_


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

class abcf(_enum.Flag, metaclass = AbcEnumMeta):
    'Enum flag for AbcMeta functionality.'

    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32

    _cleanable = before | temp | after

    def __call__(self, obj: F) -> F:
        """Add the flag to obj's meta flag with bitwise OR. Return obj for
        decorator use.."""
        return self.save(obj, self | self.read(obj))

    @classmethod
    def read(cls, obj, default: abcf|int = 0,
        /, *, attr = ABC_FLAG_ATTR
    ) -> abcf:
        "Get the flag (or `blank`) for any obj."
        return getattr(obj, attr, cls(default))

    @classmethod
    def save(cls, obj: F, value: abcf|int, /, *, attr = ABC_FLAG_ATTR) -> F:
        """Write/overwrite the value, returns obj for decorator use."""
        setattr(obj, attr, cls(value))
        return obj

    def __invert__(self):
        cached = self._invert_
        value = self._value_
        if cached is not None:
            if cached[0] == value:
                return cached[1]
            self._invert_ = None
        result = super().__invert__()
        self._invert_ = value, result
        result._invert_ = result._value_, self
        return result
    # from tools.patch import _enum_flag_invert as __invert__

class HookInfo(Mapping[str, tuple[str, ...]], metaclass = AbcMeta):

    cls: TT

    __slots__ = 'cls', 'mapping', 

    @overload
    def __new__(cls: type[HookInfo], Class: TT) -> HookInfo:...

    def hooks(self):
        'Hook names ( hook, ... ).'
        return tuple(self)

    def names(self):
        'Flat sequence of class member names ( name, ... )'
        return tuple(sorted(
            name for names in self.values() for name in names
        ))

    def pairs(self):
        'Hook, name pairs: ``((hook, name), ... )``'
        return tuple(
            item for items in (
                zip(repeat(hook), names)
                for hook, names in self.items()
            )
            for item in items
        )

    def attrs(self, hook = None) -> tuple[tuple[str, FunctionType], ...]:
        '''Get the (name, member) pairs from the class attributes. If a
        hook argument is passed, returns only those relevant. If no
        argument is passed, returns a flat, de-duplicated sequence of
        (name, member) pairs.
        '''
        Class = self.cls
        m = {}
        upd = m.update
        for key in (self if hook is None else (hook,)):
            upd({
                name: getattr(Class, name)
                for name in self[key]
                if name not in m
            })
        return tuple(sorted(m.items()))

    def __repr__(self):
        return '<HookInfo[%s]>(%s)' % (self.cls.__name__, ', '.join(self.hooks()))


    @abcf.after
    def opers(cls: type[HookInfo], *_):

        from collections import defaultdict
        from functools   import wraps
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
                    oper(set(pairs(self)), set(pairs(other)))
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
    def init_provider(provcls: TT, /, *, attr = ABC_HOOKINFO_ATTR):
        'Build hook provider info.'

        builder: dict[str, set[str]] = defaultdict(set)

        for name, member in provcls.__dict__.items():

            hooks = getattr(member, attr, None)
            if not hooks:
                continue
            if not isinstance(member, FunctionType):
                raise Emsg.InstCheck(member, FunctionType)
            for hook in hooks:
                builder[hook].add(name)

        if len(builder):
            return dict(
                (hook, tuple(sorted(builder[hook])))
                for hook in sorted(builder)
            )

    @static
    def init_implcls(implcls: TT, initial: dict[type, dict[str, F]] = None,
        /, *, attr = ABC_HOOKIMPL_ATTR):
        'Build hook implementer info.'

        # provcls -> hook -> implfunc
        builder: dict[type, dict[str, F]] = defaultdict(dict)

        impl_ns = implcls.__dict__

        if initial is not None:
            # An initial mapping can be passed, which will be merged.
            builder.update((key, value.copy()) for key, value in initial.items())

        for implfunc in impl_ns.values():
            # Scan each member in the sub class ns for the attribute.
            value: dict[type, set[str]] = getattr(implfunc, attr, None)
            if not value:
                continue
            for provcls, hooks in value.items():
                provinfo = HookInfo(provcls)
                for hook in hooks:
                    # Check valid hook for provider class
                    if hook not in provinfo:
                        raise TypeError from Emsg.MissingKey(hook)
                    # Check for duplicates. A function can implement several
                    # hooks, but each hook can be implemented by at most
                    # one function.
                    if hook in builder[provcls]:
                        raise TypeError from Emsg.DuplicateKey(hook)
                    builder[provcls][hook] = implfunc

        if len(builder):
            return dict(builder)

    @static
    def _connect_impl(implcls: type, provcls: type, implmap: Mapping[str, F]):
        'Connect the implementing hooks to a provider class.'

        provinfo = HookInfo(provcls)
        impl_ns = implcls.__dict__

        check = HookInfo._precopy_check
        fshouldcopy = HookInfo._should_copy_func

        for hook, implfunc in implmap.items():

            # Find the functions that provide the hook
            for provname, provfunc in provinfo.attrs(hook):

                check(provfunc, hook, implfunc)
                # print('')
                # print('provider - ', provcls)
                # print('implcls - ', implcls)
                if fshouldcopy(implcls, provcls, provname, provfunc):
                    # Copy the function
                    # print('Copying', provfunc)
                    compfunc = abcm.copyfunc(provfunc)
                    setattr(implcls, provname, compfunc)
                else:
                    # print('NOT Copying', provfunc)
                    # Use the impl's copy.
                    compfunc = impl_ns[provname]
                # print(compfunc, id(compfunc), id(provfunc), provfunc)
                # print('   ', compfunc.__kwdefaults__)
                # Update the kwdefaults.
                compfunc.__kwdefaults__[hook] = implfunc

                # print('   ', compfunc.__kwdefaults__)
                # print('\n')

    @static
    def _precopy_check(provfunc: F, hook: str, implfunc: F):
        # Check the existing kwdefault value.
        kwvalue = provfunc.__kwdefaults__[hook]
        if kwvalue is not None:
            if kwvalue is implfunc:
                return
            # Protection until the behavior is defined.
            raise TypeError from Emsg.ValueConflictFor(hook, implfunc, kwvalue)

    @static
    def _should_copy_func(implcls: type, provcls: type, provname: str, provfunc: F):
        impl_ns = implcls.__dict__
        if provname not in impl_ns:
            return True
        impl_value = impl_ns[provname]
        if impl_value == provfunc:
            return True
        if impl_value == provcls.__dict__.get(provname):
            return True
        return False

    @static
    @overload
    def all() -> Mapping[type, Mapping[str, tuple[str, ...]]]: ...

    @abcf.before
    def ini(ns: dict, *_):

        from functools import wraps

        providers:     dict[type, dict    [str, tuple[str, ...]]] = {}
        main     :     dict[type, MapProxy[str, tuple[str, ...]]] = {}

        init_provider_main = ns['init_provider']

        @wraps(init_provider_main)
        def init_provider(provcls: TT):

            if provcls in providers:
                raise TypeError('HookInfo already configured for %s' % provcls)

            prov_hookinfo = init_provider_main(provcls)
    
            if prov_hookinfo:
                providers[provcls] = prov_hookinfo
                main[provcls] = MapProxy(prov_hookinfo)

        # * * * * * * * * * * * * 

        implclasses = {}

        _connect_impl = ns.pop('_connect_impl')

        init_implcls_main = ns['init_implcls']

        @wraps(init_implcls_main)
        def init_implcls(implcls: TT, initial: dict = None):

            if implcls in implclasses:
                raise TypeError('Hook impl config already processed for %s' % implcls)

            impl_hookinfo: dict[type, dict[str, F]] = init_implcls_main(implcls, initial)

            if not impl_hookinfo:
                return

            implclasses[implcls] = MapProxy(impl_hookinfo)

            for provcls, implmap in impl_hookinfo.items():
                _connect_impl(implcls, provcls, implmap)
            
        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

        from collections import defaultdict

        proxy  : MapProxy[type, MapProxy[str, tuple[str, ...]]] = MapProxy(main)

        instances: dict[type, HookInfo] = {}
        caches   : dict[type, dict]  = defaultdict(dict)

        @wraps(ns['__new__'])
        def __new__(cls: type[HookInfo], Class: type):
            try:
                return instances[Class]
            except KeyError:
                pass
            try:
                mapping = proxy[Class]
            except KeyError:
                raise TypeError("No hooks defined for class '%s'" % Class)
            inst = instances[Class] = super().__new__(cls)
            inst.cls = Class
            inst.mapping = mapping
            caches[Class] = {}
            return inst

        def cachef(func, name):

            @wraps(func)
            def f(self: HookInfo, *args):
                cache = caches[self.cls]
                try:
                    return cache[name, args]
                except KeyError:
                    pass
                return cache.setdefault((name, args), func(self, *args))
            return f

        for name in ('hooks', 'names', 'pairs', 'attrs', '__repr__'):
            ns[name] = cachef(ns[name], name)

        def clearcaches():
            caches.clear()
            instances.clear()

        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #

        ns.update(
            all           = static(wraps(ns['all'])(lambda: proxy)),
            init_provider = static(init_provider),
            init_implcls  = static(init_implcls),
            _clearcaches  = static(clearcaches),
            __new__ = __new__,
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


class FlagEnum(_enum.Flag, AbcEnum):
    __slots__ = '_value_', '_invert_', 'name', 'value'
    # from tools.patch import _enum_flag_invert as __invert__


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

# Type vars

# AbcEnum boud.
EnT = TypeVar('EnT', bound = AbcEnum)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  #


del(
    _abc, _enum, TypeVar, ParamSpec,

)