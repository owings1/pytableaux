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
# pytableaux - tools.hooks module
from __future__ import annotations

__all__ = 'hookutil',

# Allowed local imports: errors, tools.abcs
from errors import Emsg, instcheck
from tools.abcs import (
    ABC_HOOKINFO_ATTR,
    ABC_HOOKUSER_ATTR,
    T,
    TT,
    abcf,
    AbcMeta,
    MapProxy,
    closure,
    overload,
    static,
)

from collections import defaultdict
from collections.abc import Set
from functools import wraps
from itertools import filterfalse, repeat
import operator as opr
from types import FunctionType
from typing import (
    Any,
    Callable,
    ClassVar,
    Collection,
    Iterator,
    Literal,
    Mapping,
    TypedDict,
)

class HookProvider(Mapping[str, tuple[str, ...]], metaclass = AbcMeta, skiphooks = True):
    'Mapping view and query API for hook provider.'

    __slots__ = 'provider', 'mapping'

    #: All base mappings.
    Providers: ClassVar[_ProvidersProxy] # populated after hookutil init

    #: The provider class.
    provider: type
    #: The base mapping.
    mapping: _ProviderInfo
    #: User connections base mapping.
    xmap: Mapping[type, _HookConns] # populated after hookutil init

    def __new__(cls, provider: type, /):
        try:
            mapping = cls.Providers[provider]
        except KeyError:
            raise Emsg.MissingValue(provider)
        inst = super().__new__(cls)
        inst.provider = provider
        inst.mapping = mapping
        return inst

    def hooknames(self, attrname: str = None, /) -> list[str]:
        'Hook names.'
        if attrname is None:
            return list(self)
        return sorted(set(hookname
            for hookname, attrnames in self.items()
            if attrname in attrnames
        ))

    def attrnames(self, hookname: str = None, /) -> list[str]:
        'Flat sequence of class attr names'
        if hookname is not None:
            return list(self[hookname])
        return sorted(set(attrname
            for attrnames in self.values()
                for attrname in attrnames
        ))

    def hookattrs(self) -> list[tuple[str, str]]:
        'Hookname, attrname pairs'
        return list(item
            for items in (
                zip(repeat(hookname), attrnames)
                    for hookname, attrnames in self.items()
                )
                for item in items
        )

    def attrs(self, hookname: str = None, /) -> list[tuple[str, FunctionType]]:
        'The (name, member) pairs from the class attributes.'
        p = self.provider
        return [
            (attrname, getattr(p, attrname))
            for attrname in self.attrnames(hookname)
        ]

    def users(self) -> list[type]:
        'List the user classes.'
        return list(self.xmap.keys())

    def connections(self,
        user: type = None,
        *,
        hookname: str = None,
        attrname: str = None,
        sortkey: Callable[[_Conn], Any] = opr.itemgetter('attrname'),
        reverse = False):
        'List user connection details.'
        it = (
            conn
                for usermap in (
                        self.xmap.values()
                    if user is None else
                        (self.xmap[user],)
                )
                    for conns in usermap.values()
                        for conn in conns
        )
        if hookname is not None:
            it = filter(lambda c: c['hookname'] == hookname, it)
        if attrname is not None:
            it = filter(lambda c: c['attrname'] == attrname, it)
        return sorted(it, key = sortkey, reverse = reverse)


    def excluding(self, hooknames: Set[str],/):
        'Return the mapping excluding the specified hooknames (__sub__).'
        instcheck(hooknames, Set)
        return {
            key: self[key]
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
            len(self.xmap),
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
    def opers(cls: type[HookProvider]): # type: ignore

        def build(items: Collection[tuple[str, str]]):
            'Build the output mapping'
            builder: dict[str, list] = defaultdict(list)
            for hookname, attrname in items:
                builder[hookname].append(attrname)
            return {key: tuple(values) for key, values in builder.items()}

        flatten = cls.hookattrs
        set_opers = dict(__sub__ = cls.excluding, __and__ = cls.only)

        for opername in ('__or__', '__and__', '__sub__', '__xor__'):

            oper = getattr(opr, opername)

            @wraps(oper)

            def f(self, other, /, *, oper: Callable[[T, T], T] = oper, set_oper = set_opers.get(opername)):
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

    @staticmethod
    def provider_info(provider: type) -> HookProvider:
        return HookProvider(provider)

    @staticmethod
    @overload
    def init_provider( # type: ignore
        provider: TT,
        initial: Mapping[str, Collection[str]]|Literal[abcf.inherit] = None,
    /) -> TT:...

    @staticmethod
    @overload
    def init_user( # type: ignore
        user: TT,
        initial: Mapping[type, Mapping[str, Callable]] = None,
    /) -> TT:...

    #******  API Closure

    @abcf.before

    def prepare(ns: dict, bases): # type: ignore

        providers   : _ProvidersTable = {}
        users       : _UsersTable = {}
        connections : _ConnsTable = {}

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

            def build(provider: type, initial: Mapping|Literal[abcf.inherit]|None, /):

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

            connect : Callable[..., dict[str, list[_Conn]]] = ns.pop('connect')

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
                        connections[provider][user] = MapProxy({ # type: ignore
                            hookname: tuple(map(MapProxy, conns))
                            for hookname, conns in
                            # Connect
                            connect(user, provider, usermap).items()
                        })
                return user

            def build(user: type, initial: Mapping|None, /, *, ATTR: str = ABC_HOOKUSER_ATTR) -> dict[type, MapProxy[str, Callable]]:

                builder: dict[type, dict[str, Callable]] = defaultdict(dict)

                if initial is not None:
                    builder.update((key, dict(value))
                        for key, value in initial.items()
                    )

                for member in user.__dict__.values():
                    # Scan each member in the sub class ns for the attribute.
                    # value: Mapping[type, Collection[str]] = getattr(member, ATTR, _EMPTY_MAP)
                    value: Mapping[type, Collection[str]] = getattr(member, ATTR, None)
                    if not value:
                        continue
                    for provider, hooknames in value.items():
                        pinfo = HookProvider(provider)
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

        #******  Populate HookProvider attributes

        @property
        def xmap(self: HookProvider):
            return MapProxy(connections[self.provider])

        for key, value in dict(
            Providers = MapProxy(providers),
            xmap = xmap,

        ).items(): setattr(HookProvider, key, value)

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * #

    #******  Closure for internal connect method.

    @abcf.temp
    @closure

    def connect():

        def connect(user: type, provider: type, usermap: Mapping[str, Callable], /):
            'Connect the implementing hooks to a provider class.'

            conns: dict[str, list[_Conn]] = defaultdict(list)
            pinfo = HookProvider(provider)
            userns = user.__dict__

            for hookname, callback in usermap.items():

                for attrname, declared in pinfo.attrs(hookname):

                    check(declared, hookname, callback)

                    if should_copy(userns, provider, attrname, declared):
                        resolved = copyfunc(declared, user.__qualname__)
                        setattr(user, attrname, resolved)
                        is_copied = True
                    else:
                        resolved = userns[attrname]
                        is_copied = False

                    resolved.__kwdefaults__[hookname] = callback

                    conns[hookname].append(_Conn(
                        provider  = provider,
                        user      = user,
                        hookname  = hookname,
                        attrname  = attrname,
                        declared  = declared,
                        resolved  = resolved,
                        is_copied = is_copied,
                        callback  = callback,
                    ))

            return dict(conns)

        def check(declared: FunctionType, hookname, callback):
            # Check the existing kwdefault value.
            value = declared.__kwdefaults__[hookname]
            if value is not None:
                if value is callback:
                    return
                # Protection until the behavior is defined.
                raise TypeError from Emsg.ValueConflictFor(hookname, callback, value)

        def should_copy(userns, provider: type, attrname, declared: FunctionType):
            if attrname not in userns:
                return True
            userns_value = userns[attrname]
            if userns_value == declared:
                return True
            if userns_value == provider.__dict__.get(attrname):
                return True
            return False

        def dund(*names:str):
            return tuple(map('__{}__'.format, names))

        import copy
        def copyfunc(f: FunctionType, ownerqn: str = None, /, *,
            fcopy: Callable[[T], T] = copy.copy,
            FATTRS_NEW : tuple[str, ...] = dund(
                'code', 'globals', 'name', 'defaults', 'closure'
            ),
            FATTRS_COPY: tuple[str, ...] = dund(
                'kwdefaults', 'annotations', 'dict', 'doc'
            ),
            FATTRS_DEL : tuple[str, ...]  = (
                ABC_HOOKINFO_ATTR,
            ),
            NOGET: object = object(),
        ) -> FunctionType:
            
            func = FunctionType(*map(f.__getattribute__, FATTRS_NEW))

            for name in FATTRS_COPY:
                value = getattr(f, name, NOGET)
                if value is not NOGET:
                    setattr(func, name, fcopy(value))

            if ownerqn is not None:
                func.__qualname__ = '%s.%s' % (ownerqn, f.__name__)

            for name in FATTRS_DEL:
                if hasattr(func, name):
                    delattr(func, name)

            return func

        return connect


# TODO: convert to dataclass.
class _Conn(TypedDict):
    provider  : type
    user      : type
    hookname  : str
    attrname  : str
    declared  : FunctionType
    resolved  : FunctionType
    is_copied : bool
    callback  : Callable

# hookname -> attrnames
_ProviderInfo = MapProxy[str, tuple[str, ...]]
# provider -> hookname -> callback
_UserInfo = MapProxy[type, MapProxy[str, Callable]]
# hookname -> (_Conn, ...)
_HookConns = MapProxy[str, tuple[_Conn, ...]]

_ProvidersTable = dict[type, _ProviderInfo]
_ProvidersProxy = MapProxy[type, _ProviderInfo]
_UsersTable = dict[type, _UserInfo]
_ConnsTable = dict[type, dict[type, _HookConns]]

del(
    closure, static, overload, wraps,
    opr,
    ABC_HOOKINFO_ATTR,
    ABC_HOOKUSER_ATTR,
)