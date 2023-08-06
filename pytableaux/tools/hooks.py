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

import functools
import operator as opr
from collections import defaultdict, deque
from collections.abc import Mapping, Set
from dataclasses import dataclass
from itertools import filterfalse, repeat
from types import FunctionType
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Callable, Collection, Literal, TypeVar

from ..errors import Emsg, check
from . import abcs, closure, dund

if TYPE_CHECKING:
    from typing import overload

# Allowed local imports: errors, tools, tools.abcs

__all__ = (
    'HookConn',
    'HookProvider',
    'hookutil')

_T = TypeVar('_T')

class HookProvider(Mapping, metaclass = abcs.AbcMeta, skiphooks = True):
    'Mapping view and query API for hook provider.'

    __slots__ = 'provider', 'mapping'

    Providers: Mapping # populated after hookutil init
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
            raise Emsg.MissingValue(provider)
        inst = super().__new__(cls)
        inst.provider = provider
        inst.mapping = mapping
        return inst

    def hooknames(self, attrname = None, /):
        'Hook names.'
        if attrname is None:
            return list(self)
        return sorted(set(hookname
            for hookname, attrnames in self.items()
                if attrname in attrnames))

    def attrnames(self, hookname = None, /):
        'Flat sequence of class attr names'
        if hookname is not None:
            return list(self[hookname])
        return sorted(set(attrname
            for attrnames in self.values()
                for attrname in attrnames))

    def hookattrs(self):
        'The (hookname, attrname) pairs.'
        return [item
            for items in (
                zip(repeat(hookname), attrnames)
                    for hookname, attrnames in self.items())
                for item in items]

    def attrs(self, hookname = None, /):
        'The (name, member) pairs from the class attributes.'
        p = self.provider
        return [(attrname, getattr(p, attrname))
            for attrname in self.attrnames(hookname)]

    def users(self):
        'List the user classes.'
        return list(self.xmap.keys())

    def connections(self, user = None, *, hookname = None, attrname = None, key = None, reverse= False):
        'List user connection details.'
        it = (conn
            for usermap in (
                    self.xmap.values()
                if user is None else
                    (self.xmap[user],))
                for conns in usermap.values()
                    for conn in conns)
        if hookname is not None:
            it = filter(lambda c: c.hookname == hookname, it)
        if attrname is not None:
            it = filter(lambda c: c.attrname == attrname, it)
        return sorted(it, key = key, reverse = reverse)

    def excluding(self, hooknames, /):
        'Return the mapping excluding the specified hooknames (__sub__).'
        check.inst(hooknames, Set)
        return {
            key: self[key]
            for key in filterfalse(hooknames.__contains__, self)}

    def only(self, hooknames, /):
        'Return the mapping with only specified hooknames (__and__).'
        return dict((key, self[key]) for key in hooknames)

    def __repr__(self):
        return '<%s[%s]>(%s):%d' % (
            type(self).__name__,
            self.provider.__name__,
            '|'.join(self.hooknames()),
            len(self.xmap))

    #******  Mapping Behavior

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, key) -> tuple[str, ...]:
        return self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __reversed__(self):
        return reversed(self.mapping)

    #******  Operators: |  &  -  ^

    @abcs.abcf.after
    def opers(cls: type[HookProvider]): # type: ignore

        def build(items):
            'Build the output mapping'
            builder = defaultdict(list)
            for hookname, attrname in items:
                builder[hookname].append(attrname)
            return {key: tuple(values) for key, values in builder.items()}

        flatten = cls.hookattrs
        set_opers = dict(__sub__ = cls.excluding, __and__ = cls.only)

        for opername in map(dund, ('or', 'and', 'sub', 'xor')):

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
                        oper(set(flatten(self)), set(flatten(other)))))
                return f
    
            setattr(cls, opername, f)


class hookutil(metaclass = abcs.AbcMeta, skiphooks = True):
    'Hook provider/user registry utils.'

    __new__ = None

    @staticmethod
    def provider_info(provider):
        return HookProvider(provider)

    if TYPE_CHECKING:
        _UserInfo = Mapping[type, Mapping[str, Callable]]
        _ProviderInfo = Mapping[str, Collection[str]]|Literal[abcs.abcf.inherit]
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

        providers = {}
        users     = {}
        connects  = {}

        #******  Closure for init_provider()

        @closure
        def provider():

            ATTR = abcs.Astr.hookinfo
            Inherit = abcs.abcf.inherit

            def init(provider, initial = None, /):
                if provider in providers:
                    raise TypeError(
                        f'Hook config already processed for {provider}')
                info = build(provider, initial)
                if len(info):
                    providers[provider] = MapProxy(info)
                    connects[provider] =  {}
                return provider

            def build(provider: type, initial, /):

                builder: dict[str, set[str]] = defaultdict(set)

                if initial is not None:
                    if initial is Inherit:
                        builder.update(inherit(provider.__bases__))
                    else:
                        builder.update((key, set(value))
                            for key, value in initial.items())

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
                    for hookname in sorted(builder)}

            def inherit(bases, /):
                builder = defaultdict(set)
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

            connect = ns.pop('connect')

            def init(user, initial = None, /):
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

            def build(user: type, initial:Mapping):

                builder = defaultdict(dict)

                if initial is not None:
                    builder.update((key, dict(value))
                        for key, value in initial.items())

                for member in user.__dict__.values():
                    # Scan each member in the sub class ns for the attribute.
                    value: Mapping = getattr(member, ATTR, None)
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
                    for (provider, usermap) in builder.items()}

            return init

        #******  Update Namespace

        ns.update(
            init_provider = staticmethod(provider),
            init_user     = staticmethod(user))

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

        def connect(user, provider, usermap: Mapping, /):
            'Connect the implementing hooks to a provider class.'

            conns = defaultdict(deque)
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
                        callback  = callback))

            return dict(conns)

        def check(declared, hookname, callback):
            # Check the existing kwdefault value.
            value = declared.__kwdefaults__[hookname]
            if value is not None:
                if value is callback:
                    return
                # Protection until the behavior is defined.
                raise TypeError from Emsg.ValueConflictFor(hookname, callback, value)

        def should_copy(userns: Mapping, provider:type, attrname, declared):
            if attrname not in userns:
                return True
            userns_value = userns[attrname]
            if userns_value == declared:
                return True
            if userns_value == provider.__dict__.get(attrname):
                return True
            return False

        import copy
        def copyfunc(f, ownerqn = None, /, *,
            fcopy = copy.copy,
            A_NEW = tuple(map(dund,
                ('code', 'globals', 'name', 'defaults', 'closure'))),
            A_CPY = tuple(map(dund,
                ('annotations', 'dict', 'doc', 'kwdefaults'))),
            A_DEL = (abcs.Astr.hookinfo,),
            NOGET = object(),
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

