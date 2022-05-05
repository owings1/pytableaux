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
pytableaux.tools.hooks
^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import functools
import operator as opr
from collections import defaultdict, deque
from collections.abc import Mapping, Set
from dataclasses import dataclass
from itertools import filterfalse, repeat
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Collection, Iterator

from pytableaux.errors import Emsg, check
from pytableaux.tools import MapProxy, abcs, closure, dund
from pytableaux.tools.typing import (TT, HkConns, HkConnsTable, HkProviderInfo,
                                     HkProviders, HkProvsTable, HkUserInfo,
                                     HkUsersTable, T)

# Allowed local imports: errors, tools, tools.abcs, tools.typing

if TYPE_CHECKING:
    from typing import Literal, overload

__all__ = (
    'HookConn',
    'HookProvider',
    'hookutil',
)

class HookProvider(HkProviderInfo, metaclass = abcs.AbcMeta, skiphooks = True):
    'Mapping view and query API for hook provider.'

    __slots__ = 'provider', 'mapping'

    Providers: ClassVar[HkProviders] # populated after hookutil init
    "All base mappings."

    provider: type
    "The provider class."

    mapping: HkProviderInfo
    "The base mapping."

    xmap: Mapping[type, HkConns] # populated after hookutil init
    "User connections base mapping."

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
        'The (hookname, attrname) pairs.'
        return [item
            for items in (
                zip(repeat(hookname), attrnames)
                    for hookname, attrnames in self.items()
                )
                for item in items
        ]

    def attrs(self, hookname: str = None, /) -> list[tuple[str, FunctionType]]:
        'The (name, member) pairs from the class attributes.'
        p = self.provider
        return [(attrname, getattr(p, attrname))
            for attrname in self.attrnames(hookname)
        ]

    def users(self) -> list[type]:
        'List the user classes.'
        return list(self.xmap.keys())

    def connections(self, user: type = None, *,
        hookname: str = None,
        attrname: str = None,
        key: Callable[[HookConn], Any] = None,
        reverse: bool = False
    ) -> list[HookConn]:
        'List user connection details.'
        it = (conn
            for usermap in (
                    self.xmap.values()
                if user is None else
                    (self.xmap[user],)
                )
                for conns in usermap.values()
                    for conn in conns
        )
        if hookname is not None:
            it = filter(lambda c: c.hookname == hookname, it)
        if attrname is not None:
            it = filter(lambda c: c.attrname == attrname, it)
        return sorted(it, key = key, reverse = reverse)

    def excluding(self, hooknames: Set[str], /) -> dict[str, tuple[str, ...]]:
        'Return the mapping excluding the specified hooknames (__sub__).'
        check.inst(hooknames, Set)
        return {
            key: self[key]
            for key in filterfalse(hooknames.__contains__, self)
        }

    def only(self, hooknames: Collection[str], /) -> dict[str, tuple[str, ...]]:
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

    @abcs.abcf.after
    def opers(cls: type[HookProvider]): # type: ignore

        def build(items: Collection[tuple[str, str]]):
            'Build the output mapping'
            builder: dict[str, list] = defaultdict(list)
            for hookname, attrname in items:
                builder[hookname].append(attrname)
            return {key: tuple(values) for key, values in builder.items()}

        flatten = cls.hookattrs
        set_opers = dict(__sub__ = cls.excluding, __and__ = cls.only)

        for opername in dund('or', 'and', 'sub', 'xor'):

            @closure
            def f():
                oper = getattr(opr, opername)
                set_oper = set_opers.get(opername)
                @functools.wraps(oper)
                def f(self, other):
                    if type(other) is not cls:
                        if set_oper is not None and isinstance(other, Set):
                            return set_oper(self, other)
                        return NotImplemented
                    return build(sorted(
                        oper(set(flatten(self)), set(flatten(other)))
                    ))
                return f
    
            setattr(cls, opername, f)


class hookutil(metaclass = abcs.AbcMeta, skiphooks = True):
    'Hook provider/user registry utils.'

    __new__ = None

    #******  API

    @staticmethod
    def provider_info(provider: type, /) -> HookProvider:
        return HookProvider(provider)

    if TYPE_CHECKING:

        @staticmethod
        @overload
        def init_provider(provider: TT, initial: Mapping[str, Collection[str]] = None, /) -> TT: ...

        @staticmethod
        @overload
        def init_provider(provider: TT, initial: Literal[abcs.abcf.inherit], /) -> TT: ... # type: ignore

        @staticmethod
        @overload
        def init_user(user: TT, initial: HkUserInfo = None, /) -> TT: ... # type: ignore

    #******  API Closure

    @abcs.abcf.before

    def prepare(ns: dict, bases): # type: ignore

        providers : HkProvsTable = {}
        users     : HkUsersTable = {}
        connects  : HkConnsTable = {}

        #******  Closure for init_provider()

        @closure

        def provider():

            ATTR = abcs.Astr.hookinfo
            Inherit = abcs.abcf.inherit

            def init(provider: TT, initial: Mapping|abcs.abcf = None, /) -> TT:
                if provider in providers:
                    raise TypeError(
                        f'Hook config already processed for {provider}'
                    )
                info = build(provider, initial)
                if len(info):
                    providers[provider] = MapProxy(info)
                    connects[provider] =  {}
                return provider

            def build(provider: type, initial: Mapping|abcs.abcf|None, /) -> dict[str, tuple[str, ...]]:

                builder: dict[str, set[str]] = defaultdict(set)

                if initial is not None:
                    if initial is Inherit:
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

            def inherit(bases: tuple[type, ...], /) -> dict[str, set[str]]:
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

            ATTR = abcs.Astr.hookuser

            connect : Callable[..., dict[str, deque[HookConn]]] = ns.pop('connect')

            def init(user: TT, initial: HkUserInfo = None, /) -> TT:
                if user in users:
                    raise TypeError(f'Hook config already processed for {user}')
                info = build(user, initial)
                if len(info):
                    users[user] = MapProxy(info)
                    for provider, usermap in info.items():
                        connects[provider][user] = MapProxy({
                            hookname: tuple(conns)
                                for hookname, conns in
                                # Connect
                                connect(user, provider, usermap).items()
                        })
                return user

            def build(user: type, initial: HkUserInfo|None, /) -> dict[type, Mapping[str, Callable]]:

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
                        pinfo = HookProvider(provider)
                        for hookname in hooknames:
                            if hookname not in pinfo:
                                raise TypeError from Emsg.MissingKey(hookname)
                            if hookname in builder[provider]:
                                raise TypeError from Emsg.DuplicateKey(hookname)
                            builder[provider][hookname] = member
                    # Clean attribute.
                    delattr(member, ATTR)

                return {provider: MapProxy(usermap)
                    for (provider, usermap) in builder.items()
                }

            return init

        #******  Update Namespace

        ns.update(
            init_provider = staticmethod(provider),
            init_user     = staticmethod(user),
        )

        #******  Populate HookProvider attributes

        def xmap(self: HookProvider):
            return MapProxy(connects[self.provider])

        HookProvider.Providers = MapProxy(providers)
        HookProvider.xmap = property(xmap)

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * #

    #******  Closure for internal connect method.

    @abcs.abcf.temp
    @closure

    def connect():

        def connect(user: type, provider: type, usermap: Mapping[str, Callable], /):
            'Connect the implementing hooks to a provider class.'

            conns: dict[str, deque[HookConn]] = defaultdict(deque)
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

                    conns[hookname].append(HookConn(
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

        def check(declared: FunctionType, hookname: str, callback: Callable):
            # Check the existing kwdefault value.
            value = declared.__kwdefaults__[hookname]
            if value is not None:
                if value is callback:
                    return
                # Protection until the behavior is defined.
                raise TypeError from Emsg.ValueConflictFor(hookname, callback, value)

        def should_copy(userns: Mapping, provider: type, attrname: str, declared: FunctionType) -> bool:
            if attrname not in userns:
                return True
            userns_value = userns[attrname]
            if userns_value == declared:
                return True
            if userns_value == provider.__dict__.get(attrname):
                return True
            return False

        import copy
        def copyfunc(f: FunctionType, ownerqn: str = None, /, *,
            fcopy: Callable[[T], T] = copy.copy,
            A_NEW: tuple[str, ...] = (*dund('code', 'globals', 'name', 'defaults', 'closure'),),
            A_CPY: tuple[str, ...] = (*dund('annotations', 'dict', 'doc', 'kwdefaults'),),
            A_DEL: tuple[str, ...]  = (abcs.Astr.hookinfo,),
            NOGET: object = object(),
        ) -> FunctionType:
            
            func = FunctionType(*map(f.__getattribute__, A_NEW))

            for name in A_CPY:
                if (value := getattr(f, name, NOGET)) is not NOGET:
                    setattr(func, name, fcopy(value))

            if ownerqn is not None:
                func.__qualname__ = f'{ownerqn}.{f.__name__}'

            for name in A_DEL:
                if hasattr(func, name):
                    delattr(func, name)

            return func

        return connect

@dataclass(order = True, frozen = True, kw_only = True, slots = True)
class HookConn(Mapping[str, Any]):
    'Hook connection data class.'

    provider: type
    "The hook provider class."

    user: type
    "The hook user class."

    hookname: str
    "The hook name."

    attrname: str
    "The hook attribute/method name."

    declared: FunctionType
    "The provider method."

    resolved: FunctionType
    "The user method."

    is_copied: bool
    "Whether `resolved` was copied."

    callback: Callable
    "The hook callback function."

    _slotset: ClassVar[frozenset]

    def __getitem__(self, key):
        if key in self._slotset:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self):
        return iter(self.__slots__)

    def __reversed__(self):
        return reversed(self.__slots__)

    def __len__(self):
        return len(self.__slots__)

HookConn._slotset = frozenset(HookConn.__slots__)
