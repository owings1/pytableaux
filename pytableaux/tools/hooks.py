# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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

from collections import defaultdict, deque
from collections.abc import Mapping, Set
from copy import copy
from dataclasses import dataclass
from itertools import filterfalse
from types import FunctionType
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Callable, Collection, TypeVar

from . import abcs, closure, dund
from .. import errors

if TYPE_CHECKING:
    from typing import overload

# Allowed local imports: errors, tools, tools.abcs

__all__ = (
    'HookConn',
    'HookProvider',
    'hookutil')

_T = TypeVar('_T')

NOGET = object()
FUNC_ARG_ATTRS = tuple(map(dund, ('code', 'globals', 'name', 'defaults', 'closure')))
FUNC_OPT_ATTRS = tuple(map(dund, ('annotations', 'dict', 'doc', 'kwdefaults')))

class HookProvider(Mapping, metaclass = abcs.AbcMeta, skiphooks = True):
    'Mapping view and query API for hook provider.'

    __slots__ = 'provider', 'mapping'

    Providers: Mapping[type] # populated after hookutil init
    "All base mappings."
    provider: type
    "The provider class."
    mapping: Mapping
    "The base mapping."
    xmap: Mapping # populated after hookutil init
    "User connections base mapping."

    def __new__(cls, provider: type, /):
        try:
            mapping = cls.Providers[provider]
        except KeyError:
            raise errors.Emsg.MissingValue(provider)
        self = super().__new__(cls)
        self.provider = provider
        self.mapping = mapping
        return self

    def attrnames(self, hookname, /):
        'Flat sequence of class attr names'
        return list(self[hookname])

    def attrs(self, hookname = None, /):
        'The (name, member) pairs from the class attributes.'
        p = self.provider
        return [(attrname, getattr(p, attrname))
            for attrname in self.attrnames(hookname)]

    def excluding(self, hooknames: Set[str], /):
        'Return the mapping excluding the specified hooknames (__sub__).'
        errors.check.inst(hooknames, Set)
        return {
            key: self[key]
            for key in filterfalse(hooknames.__contains__, self)}

    def __repr__(self):
        return '<%s[%s]>' % (type(self).__name__, self.provider.__name__)

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, key) -> tuple[str, ...]:
        return self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __reversed__(self):
        return reversed(self.mapping)

    def __sub__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        return self.excluding(other)

class hookutil(metaclass = abcs.AbcMeta, skiphooks = True):
    'Hook provider/user registry utils.'

    __new__ = None

    if TYPE_CHECKING:
        _UserInfo = Mapping[type, Mapping[str, Callable]]
        _ProviderInfo = Mapping[str, Collection[str]]
        @staticmethod
        @overload
        def init_provider(provider: type[_T]) -> type[_T]: ...
        @staticmethod
        @overload
        def init_provider(provider: type[_T], initial: _ProviderInfo) -> type[_T]: ...
        @staticmethod
        @overload
        def init_user(user: type[_T]) -> type[_T]: ...
        @overload
        @staticmethod
        def init_user(user: type[_T], initial: _UserInfo) -> type[_T]: ...

    @abcs.abcf.before
    def prepare(ns: dict, bases): # type: ignore

        providers: dict[type, Mapping[str, tuple[str, ...]]] = {}
        users: dict[type, Mapping[type, ]]     = {}
        connects  = {}

        @closure
        def init_provider():
            
            def init_provider(provider: type, initial = None, /):
                """
                A provider class exposes a hook by setting the attribute
                _abc_hook_info on each member function that will call the hook.
                The value is a set of hook names corresponding to kwargs accepted
                by the function, each with default value ``None``.
                 """
                if provider in providers:
                    raise TypeError(
                        f'Hook config already processed for {provider}')
                info = build(provider, initial)
                if len(info):
                    providers[provider] = MapProxy(info)
                    connects[provider] =  {}
                return provider

            def build(provider: type, initial: Mapping|None, /) -> dict[str, tuple[str, ...]]:
                builder: dict[str, set[str]] = defaultdict(set)

                if initial is not None:
                    builder.update((key, set(value))
                        for key, value in initial.items())

                attr = abcs.Astr.hookinfo
                for name, member in provider.__dict__.items():
                    if not isinstance(member, FunctionType):
                        continue
                    kwdefs = member.__kwdefaults__
                    hooknames = getattr(member, attr, None)
                    if hooknames:
                        if kwdefs is None:
                            raise TypeError from errors.Emsg.MissingValue('__kwdefaults__')
                        for hookname in hooknames:
                            if hookname not in kwdefs:
                                raise TypeError from errors.Emsg.MissingKey(hookname)
                            builder[hookname].add(name)
                        # Clean attribute.
                        delattr(member, attr)

                return {
                    hookname: tuple(sorted(builder[hookname]))
                    for hookname in sorted(builder)}

            return init_provider

        #******  Closure for init_user()

        @closure
        def init_user():

            connect = ns.pop('connect')

            def init(user, initial = None, /):
                """
                A class declares a hook implementation by setting the attribute
                _abc_hook_user on a callable class member, typically a function.
                The value is a mapping from the class that exposes the hook(s)
                (the provider) to a set of hook names that the function implements
                for that provider.
                """
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
                                connect(user, provider, usermap).items()})
                return user

            def build(user: type, initial:Mapping|None) -> dict[type, Mapping[str, Callable]]:

                builder = defaultdict(dict)

                if initial is not None:
                    builder.update((key, dict(value))
                        for key, value in initial.items())

                attr = abcs.Astr.hookuser
                for member in user.__dict__.values():
                    # Scan each member in the sub class ns for the attribute.
                    value: Mapping|None = getattr(member, attr, None)
                    if not value:
                        continue
                    for provider, hooknames in value.items():
                        pinfo = HookProvider(provider)
                        for hookname in hooknames:
                            if hookname not in pinfo:
                                raise TypeError from errors.Emsg.MissingKey(hookname)
                            if hookname in builder[provider]:
                                raise TypeError from errors.Emsg.DuplicateKey(hookname)
                            builder[provider][hookname] = member
                    # Clean attribute.
                    delattr(member, attr)

                return {provider: MapProxy(usermap)
                    for (provider, usermap) in builder.items()}

            return init

        #******  Update Namespace

        ns.update(
            init_provider = staticmethod(init_provider),
            init_user     = staticmethod(init_user))

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

            pinfo = HookProvider(provider)
            userns = user.__dict__
            attr = abcs.Astr.hookinfo

            conns = defaultdict(deque)

            for hookname, callback in usermap.items():

                for attrname, declared in pinfo.attrs(hookname):

                    # Check the existing kwdefault value.
                    kwvalue = declared.__kwdefaults__[hookname]
                    if kwvalue is not None:
                        raise TypeError from errors.Emsg.ValueConflictFor(hookname, callback, kwvalue)

                    if should_copy(userns, attrname, declared):
                        resolved = copyfunc(declared, user.__qualname__)
                        setattr(user, attrname, resolved)
                        if hasattr(declared, attr):
                            delattr(declared, attr)
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
                        callback  = callback))

            return dict(conns)

        def should_copy(userns: Mapping, attrname: str, declared: FunctionType) -> bool:
            try:
                # The user class directly assigns the original function, so copy.
                return declared == userns[attrname]
            except KeyError:
                # The user class does not declare the function, so copy.
                return True

        return connect

@dataclass(order = True, frozen = True, kw_only = True, slots = True)
class HookConn(Mapping):
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

    def __getitem__(self, key):
        if key in type(self).__dataclass_fields__:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self):
        return iter(type(self).__dataclass_fields__)

    def __reversed__(self):
        return reversed(type(self).__dataclass_fields__)

    def __len__(self):
        return len(type(self).__dataclass_fields__)


def copyfunc(source: FunctionType, ownerqn: str|None = None) -> FunctionType:
    func = FunctionType(*(getattr(source, name) for name in FUNC_ARG_ATTRS))
    for name in FUNC_OPT_ATTRS:
        try:
            value = getattr(source, name)
        except AttributeError:
            continue
        setattr(func, name, copy(value))
    if ownerqn is not None:
        func.__qualname__ = f'{ownerqn}.{source.__name__}'
    return func
