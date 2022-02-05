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

    # Allowed local imports: errors, tools.misc
    # ----
    from errors import (
        instcheck,
        Emsg,
    )
    # ----
    import abc as _abc
    from collections import defaultdict
    from collections.abc import Set
    import enum as _enum
    from functools import (
        reduce,
        wraps,
    )
    from itertools import (
        chain,
        islice,
        filterfalse,
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
        Collection,
        Hashable,
        Iterable,
        Iterator,
        Literal,
        Mapping,
        NamedTuple,
        Sequence,
        SupportsIndex,
        ParamSpec,
        TypedDict,
        TypeVar,
    )

if 'Types & Type Variables' or True:

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


    Func = FunctionType
    _HookProvidersTable =      dict[type, _MapProxy[str, tuple[str, ...]]]
    _HookProvidersProxy = _MapProxy[type, _MapProxy[str, tuple[str, ...]]]
    _HookUsersTable     = dict[type, _MapProxy[type, _MapProxy[str, Callable]]]

    class HookConn(TypedDict):
        user     : type
        provider : type
        hookname : str
        attrname : str
        provider_func : Func
        resolved  : Func
        is_copied : bool
        user_func : Callable

    _HookConnTable = dict[type, dict[type,  _MapProxy[str, tuple[HookConn, ...]]]]

    class EnumEntry(NamedTuple):
        'The value of the enum lookup index.'
        member : EnT
        index  : int
        nextmember: EnT | None

if 'Decorators & Utils' or True:

    _EMPTY = ()
    _EMPTY_SET = frozenset()
    _NOARG = object()
    _NOGET = object()

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
            instcheck(cls, Callable)
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

    def closure(func: Callable[..., T]) -> T:
        return func()

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

if 'Constants' or True:
    ABC_FLAG_ATTR     = '_abc_flag'
    ABC_HOOKUSER_ATTR = '_abc_hook_user'
    ABC_HOOKINFO_ATTR = '_abc_hook_info'

    ENUM_RESERVE_NAMES = frozenset(
        ('names', 'seq', '_lookup', 'index', 'indexof', 'get', 'entryof')
    )
    ENUM_HOOK_METHODS = frozenset(
        ('_member_keys', '_on_init', '_after_init')
    )

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Meta
#_____________________________________________________________________________

class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname, bases, ns: dict, /,
        hooks = None,
        skiphooks = False,
        skipflags = False,
        hookinfo = None,
        **kw
    ):
        abcm.nsinit(ns, bases, skipflags = skipflags)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        if not skiphooks:
            hookutil.init_user(Class, hooks)
        abcm.clsafter(Class, ns, skipflags = skipflags)
        if not skiphooks:
            hookutil.init_provider(Class, hookinfo)
        return Class

    def hook(cls, *hooks: str, attr = ABC_HOOKUSER_ATTR):
        'Decorator factory for tagging hook implementation (user).'
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

@static
class abcm:
    'Static meta util functions.'

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
            ns['__slots__'] = frozenset(slots)

    def clsafter(Class: TT, ns: Mapping = None, /, skipflags = False,
        deleter = type.__delattr__):
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
        *args, transform: Callable[..., T] = _thru, setter = setattr, **kw) -> T:
        value = abcm.merged_mroattr(
            subcls, name, *args, transform = transform, **kw
        )
        setter(subcls, name, value)
        return value

    def mroiter(subcls: TT, /,
        supcls: type|tuple[type, ...] = None,
        *, reverse = True, start: SupportsIndex = 0
    ) -> Iterable[TT]:
        it = subcls.mro()
        if reverse:
            it = reversed(it)
        else:
            it = iter(it)
        if supcls is not None:
            it = filter(lambda c: issubclass(c, supcls), it)
        if start != 0:
            it = islice(it, start)
        return it

    def hookable(*hooks: str, attr = ABC_HOOKINFO_ATTR):
        'Decorator factory for specifying available hooks (provider).'
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

#=============================================================================
#_____________________________________________________________________________
#
#       Enum Meta
#_____________________________________________________________________________

class AbcEnumMeta(_enum.EnumMeta):
    'General-purpose base Metaclass for all Enum classes.'

    #******  Class Instance Variables

    seq     : tuple[EnT, ...]
    _lookup : MapProxy[Any, EnumEntry]
    _member_names_: tuple[str, ...]

    @property
    def __members__(cls: type[EnT]) -> dict[str, EnT]:
        # Override to not double-proxy
        return cls._member_map_

    #******  Class Creation

    def __new__(cls, clsname, bases, ns, /, skipflags = False, **kw):

        # Run namespace init hooks.
        abcm.nsinit(ns, bases, skipflags = skipflags)

        forbid = ENUM_RESERVE_NAMES.intersection(ns)
        if forbid:
            raise TypeError('Restricted names: %s' % ', '.join(forbid))

        # Create class.
        Class = super().__new__(cls, clsname, bases, ns, **kw)

        # Run after hooks.
        abcm.clsafter(Class, ns, skipflags = skipflags)

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

    #******  Subclass Init Hooks

    def _member_keys(cls, member: EnT) -> Set[Hashable]:
        'Init hook to get the index lookup keys for a member.'
        return _EMPTY_SET

    def _on_init(cls, Class: type[EnT]):
        '''Init hook after all members have been initialized, before index
        is created. **NB:** Skips abstract classes.'''
        pass

    def _after_init(cls):
        'Init hook once the class is initialized. Includes abstract classes.'
        pass

    #******  Container Behavior

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

    #******  Class Instance Methods

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

@static
class enbm:
    'Static Enum meta utils.'

    def build_index(Class: type[EnT]) -> Mapping[Any, tuple[EnT, int, EnT|None]]:
        'Create the Enum member lookup index'
        # Fill in the member entries for all keys and merge the dict.
        # member to key set functions.
        keyfuncs = enbm.default_keys, Class._member_keys
        members = Class.seq
        return MapProxy(
            reduce(
                opr.or_,
                starmap(
                    dict.fromkeys,
                    zip(
                        # Keys -
                        #  Merges keys per member from all key funcs.
                        map(
                            set,
                            map(
                                chain.from_iterable,
                                zip(*(
                                    map(keyfunc, members)
                                    for keyfunc in keyfuncs
                                ))
                            )
                        ),
                        # Values -
                        #    Builds the member cache entry: (member, i, next-member).
                        starmap(
                            EnumEntry,
                            zip_longest(
                                members,
                                range(len(members)),
                                members[1:]
                            )
                        ),
                    )
                )
        ))

    def default_keys(member: EnT) -> Set[Hashable]:
        'Default member lookup keys'
        return {
            member.name,
            (member.name,),
            member,
            member.value
        }

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

    def cached_flag_invert(self: EnFlagT, /, *, finvert = _enum.Flag.__invert__):
        cached = self._invert_
        value = self.value
        if cached is not None:
            if cached[0] == value:
                return cached[1]
            self._invert_ = None
        result: EnFlagT = finvert(self)
        self._invert_ = value, result
        result._invert_ = result.value, self
        return result

class abcf(_enum.Flag, metaclass = AbcEnumMeta, skipflags = True):
    'Enum flag for AbcMeta functionality.'

    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32
    inherit = 64

    _cleanable = before | temp | after

    def __call__(self, obj: F):
        """Add the flag to obj's meta flag with bitwise OR. Return obj for
        decorator use."""
        return self.save(obj, self | self.read(obj))

    @classmethod
    def read(cls, obj, default: abcf|int = 0, /, *, attr = ABC_FLAG_ATTR) -> abcf:
        "Get the flag (or `blank`) for any obj."
        return getattr(obj, attr, cls(default))

    @classmethod
    def save(cls, obj: F, value: abcf|int, /, *, attr = ABC_FLAG_ATTR):
        'Write the value, returns obj for decorator use.'
        setattr(obj, attr, cls(value))
        return obj

    __invert__ = enbm.cached_flag_invert

#=============================================================================
#_____________________________________________________________________________
#
#       Hook Framework
#_____________________________________________________________________________

class HookInfo(Mapping[str, tuple[str, ...]], metaclass = AbcMeta, skiphooks = True):
    'Query hook provider & connected classes.'

    __slots__ = 'provider', 'mapping',

    #*** Populated after hookutil init.
    Providers: _HookProvidersProxy
    Users: _HookUsersTable
    _connections: Mapping[type, Mapping[str, tuple[HookConn, ...]]]
    #***

    provider: TT

    def __new__(cls, provider: TT):
        try:
            mapping = cls.Providers[provider]
        except KeyError:
            raise Emsg.MissingValue(provider)
        inst = super().__new__(cls)
        inst.provider = provider
        inst.mapping = mapping
        return inst

    def hooknames(self, attrname: str = None, /):
        'Hook names.'
        if attrname is None:
            return list(self)
        return sorted(set(hookname
            for hookname, attrnames in self.items()
            if attrname in attrnames
        ))

    def attrnames(self, hookname: str = None, /):
        'Flat sequence of class attr names'
        if hookname is not None:
            return list(self[hookname])
        return sorted(set(attrname
            for attrnames in self.values()
                for attrname in attrnames
        ))

    def hookattrs(self):
        'Hookname, attrname pairs'
        return list(item
            for items in (
                zip(repeat(hookname), attrnames)
                    for hookname, attrnames in self.items()
                )
                for item in items
        )

    def attrs(self, hookname: str = None, /) -> list[tuple[str, Func]]:
        'The (name, member) pairs from the class attributes.'
        p = self.provider
        return list((attrname, getattr(p, attrname))
            for attrname in self.attrnames(hookname)
        )

    def users(self):
        'List the user classes.'
        return list(self._connections.keys())

    def connections(self,
        user: type = None, *, hookname: str = None, attrname: str = None,
        sortkey: Callable[[HookConn], Any] = opr.itemgetter('attrname'),
        reverse = False):
        'List user connection details.'
        it = (
            conn
                for usermap in (
                        self._connections.values()
                    if user is None else
                        (self._connections[user],)
                )
                    for conns in usermap.values()
                        for conn in conns
        )
        if hookname is not None:
            it = filter(lambda c, eq = hookname.__eq__: eq(c['hookname']), it)
        if attrname is not None:
            it = filter(lambda c, eq = attrname.__eq__: eq(c['attrname']), it)
        return sorted(it, key = sortkey, reverse = reverse)


    def excluding(self, hooknames: Set[str],/):
        'Return the mapping excluding the specified hooknames (__sub__).'
        instcheck(hooknames, Set)
        return {key: self[key]
            for key in filterfalse(hooknames.__contains__, self)
        }

    def only(self, hooknames: Collection[str],/):
        'Return the mapping with only specified hooknames (__and__).'
        return dict((key, self[key]) for key in hooknames)

    def __repr__(self):
        return '<%s[%s]>(%s):%d' % (
            type(self).__name__,
            self.provider.__name__,
            '|'.join(self.hooknames()),
            len(self._connections),
        )

    #******  Mapping Behavior

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, key) -> tuple[str, ...]:
        return self.mapping[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.mapping)

    def __reversed__(self) -> Iterator[str]:
        return reversed(self.mapping)

    #******  Operators: |  &  -  ^

    @abcf.after
    def opers(cls: type[HookInfo]):

        def build(items: tuple[set[str], set[str]]):
            'Build the output mapping'
            builder: dict[str, list] = defaultdict(list)
            for hookname, attrname in items:
                builder[hookname].append(attrname)
            return {key: tuple(values) for key, values in builder.items()}

        flatten = cls.hookattrs
        set_opers = dict(__sub__ = cls.excluding, __and__ = cls.only)

        for opername in ('__sub__', '__and__', '__or__', '__xor__'):

            oper = getattr(opr, opername)

            @wraps(oper)

            def f(self, other, /, *, oper = oper, set_oper = set_opers.get(opername)):
                if type(other) is not cls:
                    if set_oper is not None and isinstance(other, Set):
                        return set_oper(self, other)
                    return NotImplemented
                return build(sorted(
                    oper(set(flatten(self)), set(flatten(other)))
                ))
    
            setattr(cls, opername, f)

@static
class hookutil(metaclass = AbcMeta, skiphooks = True):

    #******  API

    @overload
    def init_provider(
        provider: TT,
        initial: Mapping[str, Collection[str]]|Literal[abcf.inherit] = None,
    /) -> TT:...

    @overload
    def init_user(
        user: TT,
        initial: Mapping[type, Mapping[str, Callable]] = None,
    /) -> TT:...

    #******  API Closure

    @abcf.before

    def prepare(ns: dict, bases):

        providers   : _HookProvidersTable = {}
        users       : _HookUsersTable = {}
        connections : _HookConnTable = {}

        #******  Closure for init_provider()

        @closure

        def provider():

            ATTR = ABC_HOOKINFO_ATTR

            @wraps(ns.pop('init_provider'))

            def init(provider: type, initial: Mapping = None,/):
                if provider in providers:
                    raise TypeError(
                        'Hook provider config already processed for %s' % provider
                    )
                info = build(provider, initial)
                if len(info):
                    providers[provider] = MapProxy(info)
                    connections[provider] =  {}
                return provider

            def build(provider: type, initial: Mapping|abcf|None, /):

                builder: dict[str, set[str]] = defaultdict(set)

                if initial is not None:
                    if initial is abcf.inherit:
                        builder.update(inherit(provider.__bases__))
                    else:
                        builder.update((key, set(value))
                            for key, value in initial.items()
                        )

                for attrname, member in provider.__dict__.items():
                    if not isinstance(member, FunctionType):
                        continue
                    kwdefs = member.__kwdefaults__
                    hooknames = getattr(member, ATTR, None)
                    if hooknames:
                        if kwdefs is None:
                            raise TypeError from Emsg.MissingValue('__kwdefaults__')
                        for hookname in hooknames:
                            if hookname not in kwdefs:
                                raise TypeError from Emsg.MissingKey(hookname)
                            builder[hookname].add(attrname)
                        # Clean attribute.
                        delattr(member, ATTR)

                return {
                    hookname: tuple(sorted(builder[hookname]))
                    for hookname in sorted(builder)
                }

            def inherit(bases: tuple[type, ...]):
                builder: dict[str, set[str]] = defaultdict(set)
                for base in bases:
                    if base in providers:
                        for hookname, attrnames in providers[base].items():
                            builder[hookname].update(attrnames)
                return dict(builder)

            return init

        #******  Closure for init_user()

        @closure

        def user():

            ATTR = ABC_HOOKUSER_ATTR

            connect : Callable[..., dict[str, list[HookConn]]] = ns.pop('connect')

            @wraps(ns.pop('init_user'))

            def init(user: type, initial: Mapping = None,/):
                if user in users:
                    raise TypeError(
                        'Hook user config already processed for %s' % user
                    )
                info = build(user, initial)
                if len(info):
                    users[user] = MapProxy(info)

                    for provider, usermap in info.items():
                        connections[provider][user] = MapProxy({
                            hookname: tuple(map(MapProxy, conns))
                            for hookname, conns in
                            # Connect
                            connect(user, provider, usermap).items()
                        })
                return user

            def build(user: type, initial: Mapping|None,/):

                builder: dict[type, dict[str, Callable]] = defaultdict(dict)

                if initial is not None:
                    builder.update((key, dict(value))
                        for key, value in initial.items()
                    )

                for member in user.__dict__.values():
                    # Scan each member in the sub class ns for the attribute.
                    value: Mapping[type, Collection[str]] = getattr(member, ATTR, None)
                    if not value:
                        continue
                    for provider, hooknames in value.items():
                        pinfo = HookInfo(provider)
                        for hookname in hooknames:
                            if hookname not in pinfo:
                                raise TypeError from Emsg.MissingKey(hookname)
                            if hookname in builder[provider]:
                                raise TypeError from Emsg.DuplicateKey(hookname)
                            builder[provider][hookname] = member
                    # Clean attribute.
                    delattr(member, ATTR)

                return {
                    provider: MapProxy(usermap)
                    for (provider, usermap) in builder.items()
                }

            return init

        #******  Update Namespace

        ns.update(
            init_provider = static(provider),
            init_user     = static(user),
        )

        #******  Populate HookInfo attributes

        @property
        def _connections(self: HookInfo):
            return MapProxy(connections[self.provider])

        for key, value in dict(

            Providers    = MapProxy(providers),
            Users        = MapProxy(users),
            _connections = _connections,

        ).items(): setattr(HookInfo, key, value)

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * #

    #******  Closure for internal connect method.

    @abcf.temp
    @closure

    def connect():

        def connect(user: type, provider: type, usermap: Mapping[str, Callable], /):
            'Connect the implementing hooks to a provider class.'

            conns: dict[str, list[HookConn]] = defaultdict(list)
            pinfo = HookInfo(provider)
            userns = user.__dict__

            for hookname, user_func in usermap.items():

                for attrname, provider_func in pinfo.attrs(hookname):

                    check(provider_func, hookname, user_func)

                    if should_copy(userns, provider, attrname, provider_func):
                        resolved = copyfunc(provider_func, user.__qualname__)
                        setattr(user, attrname, resolved)
                        is_copied = True
                    else:
                        resolved = userns[attrname]
                        is_copied = False

                    resolved.__kwdefaults__[hookname] = user_func

                    conns[hookname].append(HookConn(
                        provider = provider,
                        user     = user,
                        hookname = hookname,
                        attrname = attrname,
                        resolved  = resolved,
                        provider_func = provider_func,
                        is_copied = is_copied,
                        user_func = user_func,
                    ))

            return dict(conns)

        def check(provider_func: Func, hookname, user_func):
            # Check the existing kwdefault value.
            value = provider_func.__kwdefaults__[hookname]
            if value is not None:
                if value is user_func:
                    return
                # Protection until the behavior is defined.
                raise TypeError from Emsg.ValueConflictFor(hookname, user_func, value)

        def should_copy(userns, provider: type, attrname, provider_func: Func):
            if attrname not in userns:
                return True
            userns_value = userns[attrname]
            if userns_value == provider_func:
                return True
            if userns_value == provider.__dict__.get(attrname):
                return True
            return False

        def dund(*names:str):
            return tuple(map('__{}__'.format, names))

        FATTRS_NEW  = dund('code', 'globals', 'name', 'defaults', 'closure')
        FATTRS_DICT = dund('kwdefaults', 'annotations', 'dict')
        FATTRS_ASGN = dund('doc')
        FATTRS_DEL  = {ABC_HOOKINFO_ATTR}
        
        def copyfunc(f: Func, ownerqn: str = None,/):
            
            func = FunctionType(*map(f.__getattribute__, FATTRS_NEW))

            for name in FATTRS_DICT:
                value = getattr(f, name, None)
                if value is not None:
                    setattr(func, name, dict(value))

            for name in FATTRS_ASGN:
                value = getattr(f, name, None)
                if value is not None:
                    setattr(func, name, value)

            if ownerqn is not None:
                func.__qualname__ = '%s.%s' % (ownerqn, f.__name__)

            for name in FATTRS_DEL:
                if hasattr(func, name):
                    delattr(func, name)

            return func

        return connect

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * #

    # @closure
    @abcf.temp
    def copy_provider_hooks():
        pass
        # def copy(ns: dict, bases: tuple[type, ...]):
        #     for pinfo in map(HookInfo, filter(HookInfo.Providers.__contains__, bases)):
        #         print('copy', pinfo.provider)
        #         for name, base_member in pinfo.attrs():
        #             if name in ns:
        #                 verify(ns[name], base_member, name, pinfo)
        #             else:
        #                 ns[name] = base_member

        # from inspect import Signature

        # def verify(ns_member: Func, base_member: Func, name: str, pinfo: HookInfo):
        #     if ns_member is base_member:
        #         return
        #     todo = set(pinfo.hooknames(name))
        #     kwdefs = ns_member.__kwdefaults__
        #     if kwdefs is not None:
        #         todo.difference_update(kwdefs)
        #         if len(todo) == 0:
        #             return
        #     params = Signature.from_callable(ns_member).parameters
        #     if len(params):
        #         p = params[next(reversed(params))]
        #         if p.kind is p.VAR_KEYWORD:
        #             return
        #     raise TypeError(
        #         '%s missing kwargs: %s' % (name, ', '.join(todo))
        #     )

        # return copy
        return

#=============================================================================
#_____________________________________________________________________________
#
#       Base Classes
#_____________________________________________________________________________

#*****  Enum Base Classes

class AbcEnum(_enum.Enum, metaclass = AbcEnumMeta):

    __slots__ = _EMPTY_SET

    _invert_: tuple[int, EnFlagT] | None
    name: str
    value: Any

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

class FlagEnum(_enum.Flag, AbcEnum):
    __slots__ = '_value_', '_invert_', 'name', 'value'
    __invert__ = enbm.cached_flag_invert
    value: int

class IntEnum(_enum.IntEnum, AbcEnum):
    __slots__ = _EMPTY_SET
    # NB: "nonempty __slots__ not supported for subtype of 'IntEnum'"
    pass

#*****  Abc Base Classes

class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'

    __slots__ = _EMPTY_SET

class Copyable(Abc):

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
        return abcm.check_mrodict(subcls.mro(), '__copy__', 'copy', '__deepcopy__')

#=============================================================================
#_____________________________________________________________________________

if 'Type Variables (deferred)' or True:
    EnT     = TypeVar('EnT',     bound = AbcEnum)
    EnFlagT = TypeVar('EnFlagT', bound = FlagEnum)

if 'Cleanup' or True:
    del(
        _abc,
        _enum,
        TypeVar,
        ParamSpec,
    )