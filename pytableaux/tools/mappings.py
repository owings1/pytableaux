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
pytableaux.tools.mappings
^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Collection, Iterator, Mapping, MutableMapping, Set
from itertools import chain, filterfalse
from operator import not_, truth
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable

from pytableaux.errors import Emsg, check
from pytableaux.tools import MapProxy, abcs, closure, isattrstr, true, thru
from pytableaux.tools.decorators import membr, wraps
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.typing import KT, VT, NotImplType, T

if TYPE_CHECKING:
    from typing import overload
    from pytableaux.tools.typing import MapiT, MapT, SetT

__all__ = (
    'defaultdmap',
    'DequeCache',
    'dmap',
    'dmapattr',
    'dmapns',
    'ItemMapEnum',
    'ItemsIterator',
    'KeySetAttr',
    'MapCover',
    'MappingApi',
    # 'MapProxy',
    'MutableMappingApi',
)

class MappingApi(Mapping[KT, VT], abcs.Copyable):

    __slots__ = EMPTY_SET

    if TYPE_CHECKING:
        @overload
        def __or__(self:  MapT, b: Mapping) -> MapT: ...
        @overload
        def __ror__(self: MapT, b: Mapping) -> MapT: ...
        @overload
        def __ror__(self: MapT, b: SetT) -> SetT: ...

        @overload
        def __mod__(self: MapT, b: Mapping) -> MapT: ...
        @overload
        def __rmod__(self: MapT, b: Mapping) -> MapT: ...

        @overload
        def __and__(self:  MapT, b: SetT) -> MapT: ...
        @overload
        def __sub__(self:  MapT, b: SetT) -> MapT: ...

        @overload
        def __rand__(self: MapT, b: SetT) -> SetT: ...
        @overload
        def __rsub__(self: MapT, b: SetT) -> SetT: ...
        @overload
        def __rxor__(self: MapT, b: SetT) -> SetT: ...

    @abcs.abcf.temp
    @membr.defer
    def oper(member: membr[type[MappingApi]]):
        opname = member.name
        @wraps(member)
        def f(self, other, /):
            return _opcache.resolve(self, opname, other)
        return f

    __or__ = __ror__ = __and__ = __rand__ = __sub__ = __rsub__ = \
         __rxor__ = __mod__ = __rmod__ = oper()

    def __or__op__(self, other: Mapping):
        'Mapping | Mapping -> Mapping'
        return chain(ItemsIterator(self), ItemsIterator(other))

    def __ror__op__(self, other: Mapping|Set):
        'Set     | Mapping --> Set'
        if isinstance(other, Set): return chain(other, self)
        'Mapping | Mapping --> Mapping'
        return chain(ItemsIterator(other), ItemsIterator(self))

    def __mod__op__(self, other: Mapping):
        'Mapping | Mapping -> Mapping'
        return chain(ItemsIterator(self), ItemsIterator(other, 
            kpred = self.__contains__, koper = not_
        ))

    def __rmod__op__(self, other: Mapping):
        'Mapping | Mapping -> Mapping'
        if not isinstance(other, Mapping): return NotImplemented
        return chain(ItemsIterator(other), ItemsIterator(self,
            kpred = other.__contains__, koper = not_
        ))

    def __and__op__(self, other: Set):
        if not isinstance(other, Set): return NotImplemented
        'Mapping & Set    --> Mapping'
        return ItemsIterator(self, kpred = other.__contains__)

    def __rand__op__(self, other: Set):
        if not isinstance(other, Set): return NotImplemented
        'Set    & Mapping --> Set'
        return filter(self.__contains__, other)

    def __sub__op__(self, other: Set):
        if not isinstance(other, Set): return NotImplemented
        'Mapping - Set --> Mapping'
        return ItemsIterator(self, kpred = other.__contains__, koper = not_)

    def __rsub__op__(self, other: Set):
        if not isinstance(other, Set): return NotImplemented
        'Set    - Mapping --> Set'
        return filterfalse(other, self.__contains__)

    def __rxor__op__(self, other: Set):
        if not isinstance(other, Set): return NotImplemented
        'Set   ^ Mapping --> Set'
        return chain(
            filterfalse(self.__contains__, other),
            filterfalse(other.__contains__, self),
        )

    def copy(self):
        return self._from_mapping(self)

    def _asdict(self) -> dict[KT, VT]:
        'Compatibility for JSON serialization.'
        return dict(self)

    @classmethod
    def _from_mapping(cls: type[MapT], mapping: Mapping) -> MapT:
        'Construct a new instance from a mapping.'
        return cls(mapping)

    @classmethod
    def _from_iterable(cls: type[MapT], it: Iterable[tuple[Any, Any]], /) -> MapT:
        'Construct a new instance from an iterable of item tuples.'
        return NotImplemented

    @classmethod
    def _oper_res_type(cls, othrtype: type[Iterable], /) -> type[Mapping]:
        '''Return the type (or callable) to construct a new instance from the result
        of an arithmetic operator expression for objects of type cls on the left hand
        side, and of othrtype on the right hand side.'''
        return cls

    @classmethod
    def _roper_res_type(cls, othrtype: type[Iterable], /) -> type[Mapping]:
        '''Return the type (or callable) to construct a new instance from the result
        of an arithmetic operator expression for objects of type cls on the right hand
        side, and of othrtype on the left hand side.'''
        if issubclass(othrtype, Set):
            return othrtype
        return cls._oper_res_type(othrtype)


class MapCover(MappingApi[KT, VT]):
    'Mapping reference.'

    __slots__ = '__len__', '__getitem__', '__iter__', '__reversed__'

    _cover_items: ClassVar[tuple[tuple[str, str]]] = tuple(zip(__slots__, __slots__))
    _cover_attrs: ClassVar[setf[str]] = setf(dict(_cover_items).values())

    def __init__(self, mapping: Mapping[KT, VT] = None, /, **kwmap):
        if mapping is None:
            mapping = kwmap
        else:
            check.inst(mapping, Mapping)
            if len(kwmap):
                raise TypeError('Expected mapping or kwargs, not both.')
        self._init_cover(mapping, self)

    @classmethod
    def _init_cover(cls, src: Mapping, dest: Any, /, *,
        ga = object.__getattribute__,
        sa = object.__setattr__
    ):
        for srcname, destname in cls._cover_items:
            sa(dest, destname, ga(src, srcname))

    def __delattr__(self, name, /):
        if name in self._cover_attrs:
            raise Emsg.ReadOnly(self, name)
        super().__delattr__(name)

    def __setattr__(self, name, value, /):
        if name in self._cover_attrs:
            raise Emsg.ReadOnly(self, name)
        super().__setattr__(name, value)

    def __repr__(self):
        return repr(self._asdict())

    @classmethod
    def _from_iterable(cls, it):
        return cls._from_mapping(dict(it))

    def __init_subclass__(subcls: type[MapCover], **kw):
        super().__init_subclass__(**kw)
        if isinstance(subcls._cover_items, Mapping):
            subcls._cover_items = tuple(subcls._cover_items.items())
        subcls._cover_attrs = setf(dict(subcls._cover_items).values())

class MutableMappingApi(MappingApi[KT, VT], MutableMapping[KT, VT], abcs.Copyable):

    __slots__ = EMPTY_SET

    def __or__op__(self, other):
        if self._oper_res_type(type(other)) is type(self):
            inst = self.copy()
            inst.update(other)
            return inst
        return super().__or__op__(other)

    def __ror__op__(self, other):
        if self._roper_res_type(type(other)) is type(self):
            inst = self.copy()
            inst.update(other)
            return inst
        return super().__ror__op__(other)

    def __ior__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        self.update(other)
        return self

    def __imod__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        self.update(ItemsIterator(other, kpred = self.__contains__, koper = not_))
        return self

    def __iand__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        for _ in map(self.__delitem__,
            tuple(filterfalse(other.__contains__, self))
        ): pass
        return self

    def __isub__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        for _ in map(self.__delitem__,
            tuple(filter(self.__contains__, other))
        ): pass
        return self

    @closure
    def _setitem_update():
        EMPTY_ITER = iter(())
        def update(self, it: Iterable = None, /, **kw):
            '''Alternate 'update' implementation for classes that need more control'''
            if it is None:
                it = EMPTY_ITER
            else:
                it = ItemsIterator(it)
            if len(kw):
                it = chain(it, ItemsIterator(kw))
            setitem = self.__setitem__
            for key, value in it:
                setitem(key, value)
        return update

    @classmethod
    def _from_iterable(cls, it):
        return cls(it)

class dmap(dict[KT, VT], MutableMappingApi[KT, VT]):
    'Mutable mapping api from dict.'

    __slots__ = EMPTY_SET

    copy    = MutableMappingApi.copy
    __or__  = MutableMappingApi[KT, VT].__or__
    __ror__ = MutableMappingApi[KT, VT].__ror__

class defaultdmap(defaultdict[KT, VT], MutableMappingApi[KT, VT]):
    'Mutable mapping api from defaultdict.'

    __slots__ = EMPTY_SET

    copy    = MutableMappingApi.copy
    __or__  = MutableMappingApi[KT, VT].__or__
    __ror__ = MutableMappingApi[KT, VT].__ror__

    @classmethod
    def _from_mapping(cls, mapping, /):
        if isinstance(mapping, defaultdict):
            return cls(mapping.default_factory, mapping)
        return cls(None, mapping)

    @classmethod
    def _from_iterable(cls, it, /):
        return cls(None, it)

    @classmethod
    def _roper_res_type(cls, othrtype, /):
        if issubclass(othrtype, Mapping):
            return dmap
        return super()._roper_res_type(othrtype)

class KeySetAttr(abcs.Abc):

    __slots__ = EMPTY_SET

    def __setitem__(self, key, value, /):
        super().__setitem__(key, value)
        if isattrstr(key) and self._keyattr_ok(key):
            super().__setattr__(key, value)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self._keyattr_ok(name):
            super().__setitem__(name, value)

    def __delitem__(self, key, /):
        super().__delitem__(key)
        if isattrstr(key) and self._keyattr_ok(key):
            super().__delattr__(key)

    def __delattr__(self, name):
        super().__delattr__(name)
        if self._keyattr_ok(name) and name in self:
            super().__delitem__(name)

    if TYPE_CHECKING:
        @overload
        def update(self, it: Iterable = None, /, **kw):...

    update = MutableMappingApi._setitem_update

    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:
        'Return whether it is ok to set the attribute name.'
        return not hasattr(cls, name)

class dmapattr(KeySetAttr, dmap[KT, VT]):
    __slots__ = EMPTY_SET

class dmapns(dmapattr[KT, VT]):

    def __init__(self, it: Iterable = None, **kw):
        if it is not None:
            self.update(it)
        if len(kw):
            self.update(kw)

    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:
        return len(name) and name[0] != '_'

class ItemMapEnum(abcs.Ebc):
    """Fixed mapping enum based on item tuples.

    If a member value is defined as a mapping, the member's ``_value_`` attribute
    is converted to a tuple of item tuples during ``__init__()``.

    Implementations should always call ``super().__init__()`` if it is overridden.

    Math operators ``|``, ``&``, ``-``, ``%``, and ``^`` are implemented like
    ``MappingApi``, including right-hand operators. Mapping operators ``|`` and
    ``^`` return a ``dict`` instance by default, which can be overridden via the
    ``_oper_res_type()`` class method.

    The methods ``_from_mapping()`` and ``_from_iterable()`` are **not** added.
    These methods would not be called internally by operator methods, since we
    always resolve to a ``dict`` (not our own class).

    Note that ``.get()`` is implemented as ``.iget()``, since ``AbcEnumMeta``
    uses ``'get'`` as a class method to lookup enum members.
    """

    __slots__ = (
        '__iter__', '__getitem__', '__len__', '__reversed__',
        'name', 'value', '_value_'
    )

    if TYPE_CHECKING:
        @overload
        def __init__(self, mapping: Mapping): ...
        @overload
        def __init__(self, *items: tuple[Any, Any]): ...

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Mapping):
            self._value_ = args = tuple(args[0].items())
        m = dict(args)
        self.__len__ = m.__len__
        self.__iter__ = m.__iter__
        self.__getitem__ = m.__getitem__
        self.__reversed__ = m.__reversed__

    keys = MappingApi.keys
    items = MappingApi.items
    values = MappingApi.values
    iget = MappingApi.get # get() is not allowed for Ebc

    _asdict = MappingApi._asdict

    __or__ = MappingApi.__or__
    __ror__ = MappingApi.__ror__
    __or__op__ = MappingApi.__or__op__
    __ror__op__ = MappingApi.__ror__op__

    __mod__ = MappingApi.__mod__
    __rmod__ = MappingApi.__rmod__
    __mod__op__ = MappingApi.__mod__op__
    __rmod__op__ = MappingApi.__rmod__op__

    __and__ = MappingApi.__and__
    __rand__ = MappingApi.__rand__
    __and__op__ = MappingApi.__and__op__
    __rand__op__ = MappingApi.__rand__op__

    __sub__ = MappingApi.__sub__
    __rsub__ = MappingApi.__rsub__
    __sub__op__ = MappingApi.__sub__op__
    __rsub__op__ = MappingApi.__rsub__op__

    __rxor__ = MappingApi.__rxor__
    __rxor__op__ = MappingApi.__rxor__op__

    _roper_res_type = classmethod(MappingApi._roper_res_type.__func__)

    @classmethod
    def _oper_res_type(cls, othrtype: type[Iterable], /):
        return dict

class DequeCache(Collection[VT], abcs.Abc):

    __slots__ = (
        '__len__', '__getitem__',
        '__reversed__',
        '__setitem__', '__iter__', '__contains__',
        'clear', '_maxlen',
    )

    @property
    def maxlen(self) -> int:
        return self._maxlen

    def __init__(self, maxlen = 10):

        idx  : dict[Any, VT] = {}
        rev  : dict[VT, set] = {}
        deck : deque[VT] = deque(maxlen = maxlen)

        self._maxlen = maxlen

        self.__len__ = deck.__len__
        self.__iter__ = deck.__iter__
        self.__reversed__ = deck.__reversed__
        self.__contains__ = rev.__contains__
        self.__getitem__ = idx.__getitem__

        def clear():
            idx.clear()
            rev.clear()
            deck.clear()

        def setitem(key, item: VT):
            if item in self:
                item = self[item]
            else:
                if len(self) == self.maxlen:
                    old = deck.popleft()
                    for k in rev.pop(old): del(idx[k])
                idx[item] = item
                rev[item] = {item}
                deck.append(item)
            idx[key] = item
            rev[item].add(key)

        self.clear = clear
        self.__setitem__ = setitem


class ItemsIterator(Iterator[tuple[KT, VT]]):
    'Mapping items iterator.'

    __slots__ = '_gen_',

    def __new__(cls, obj, /, *args, **kw):
        if type(obj) is cls and not len(args) and not len(kw):
            return obj
        return super().__new__(cls)

    def __init__(self,
        obj: Mapping[KT, VT]|Iterable[tuple[KT, VT]]|Iterable[KT],
        /, *, 
        vget: Callable[[KT], VT]|None = None,
        kpred: Callable[[KT], bool] = true,
        vpred: Callable[[VT], bool] = true,
        koper: Callable[[bool], bool] = truth,
        voper: Callable[[bool], bool] = truth,
    ):
        if vget is None:
            if hasattr(obj, 'keys'):
                self._gen_ = self._gen1(
                    obj.keys, obj.__getitem__, kpred, vpred, koper, voper
                )
            else:
                self._gen_ = self._gen2(
                    obj, kpred, vpred, koper, voper
                )
        else:
            self._gen_ = self._gen1(
                obj.__iter__, vget, kpred, vpred, koper, voper
            )

    def __iter__(self):
        return self

    def __next__(self) -> tuple[KT, VT]:
        return self._gen_.__next__()

    @staticmethod
    def _gen1(getkeys, vget, kpred, vpred, koper, voper):
        for k in getkeys():
            if koper(kpred(k)):
                v = vget(k)
                if voper(vpred(v)):
                    yield k, v

    @staticmethod
    def _gen2(items, kpred, vpred, koper, voper):
        for k, v in items:
            if koper(kpred(k)) and voper(vpred(v)):
                yield k, v

if 'Operators Cache' or True:

    def _checklimit(length: int, /, *, _limit = 50):
        return length > _limit and length > 0

    class _CacheResolversType(dict[tuple[Callable, Callable], Callable]):

        __slots__ = EMPTY_SET

        def __missing__(self, pair: tuple[Callable, Callable], /, *,
            checklimit: Callable[[int], bool] = _checklimit
        ):
            while checklimit(len(self)):
                self.pop(next(iter(self)))
            res_create, get_res_iter = pair
            def cached_resolver(mapi, other):
                return res_create(get_res_iter(mapi, other))
            cached_resolver.__qualname__ = cached_resolver.__name__
            return self.setdefault(pair, cached_resolver)

    _ResolverFactory = _CacheResolversType()

    class _FuncCache(dict[type[Iterable], Callable[[MappingApi, Iterable], Iterable|NotImplType]]):

        __slots__ = setf(('get_res_iter', 'get_res_type'))

        get_res_iter: Callable[[MappingApi, Iterable], Iterable|Mapping|NotImplType]
        get_res_type: Callable[[type], type|NotImplType]

        def __init__(self, mapitype: type[MappingApi], opname: str, /):
            self.get_res_iter = getattr(mapitype, opname + 'op__')
            if opname.startswith('__r'):
                self.get_res_type = mapitype._roper_res_type
            else:
                self.get_res_type = mapitype._oper_res_type

        def __missing__(self, othrtype: type[Iterable], /, *,
            checklimit: Callable[[int], bool] = _checklimit
        ):
            while checklimit(len(self)):
                self.pop(next(iter(self)))
            return self.setdefault(othrtype, self.resolve)

        def resolve(self, mapi, other, /, *,
            FTHRU: Callable[[T], T] = thru,
            ResolverFactory: _CacheResolversType = _ResolverFactory,
        ):
            othrtype = type(other)
            if not issubclass(othrtype, Iterable):
                return self.reject(othrtype)
            res_type = self.get_res_type(othrtype)
            if res_type is NotImplemented:
                return self.reject(othrtype)
            get_res_iter = self.get_res_iter
            it = get_res_iter(mapi, other)
            if (
                it is not self and it is not other and
                isinstance(res_type, type) and isinstance(it, res_type)
            ):
                res_create = FTHRU
            elif isinstance(it, Mapping):
                res_create = getattr(res_type, '_from_mapping', res_type)
            elif isinstance(it, Iterable):
                res_create = getattr(res_type, '_from_iterable', res_type)
            elif it is NotImplemented:
                return self.reject(othrtype)
            else:
                raise Emsg.InstCheck(it, Iterable)
            res = res_create(it)
            self[othrtype] = ResolverFactory[res_create, get_res_iter]
            return res

        @closure
        def reject():

            def FNOTIMPL(*args, **kw):
                return NotImplemented

            def reject(self: _FuncCache, othrtype: type[Iterable], /, *,
                FNOTIMPL: Callable[..., NotImplType] = FNOTIMPL
            ):
                self[othrtype] = FNOTIMPL
                return NotImplemented

            return reject

    class _TypeFuncsCache(dict[str, _FuncCache]):

        __slots__ = setf({'mapitype'})

        def __init__(self, mapitype: type[MappingApi]):
            self.mapitype = mapitype

        def __missing__(self, opname: str, /, *,
            _FuncCache: type[_FuncCache] = _FuncCache
        ):
            return self.setdefault(opname, _FuncCache(self.mapitype, opname))

    class _OperFuncsCache(dict[type[MappingApi], _TypeFuncsCache]):

        __slots__ = EMPTY_SET

        def __missing__(self, mapitype: type[MappingApi], /, *,
            _TypeFuncsCache: type[_TypeFuncsCache] = _TypeFuncsCache,
            checklimit: Callable[[int], bool] = _checklimit,
        ):
            while checklimit(len(self)):
                self.pop(next(iter(self)))
            return self.setdefault(mapitype, _TypeFuncsCache(mapitype))

    @closure
    def _opcache():

        source = _OperFuncsCache()
        resolvers = _ResolverFactory
        checklimit = _checklimit

        class opercache:

            @staticmethod
            def get(
                mapitype: type[MapiT], opname: str, othrtype: type[T],
            /) -> Callable[[MapiT, T], MapiT|NotImplType]:
                return source[mapitype][opname][othrtype]

            @staticmethod
            def resolve(mapi: MapiT, opname: str, other: T, / ) -> MapiT|NotImplType:
                return source[type(mapi)][opname][type(other)](mapi, other)

            @staticmethod
            def copy():
                return {
                    k: {k: dict(v) for k, v in v.items()}
                    for k, v in source.items()
                }

            @staticmethod
            def resolvers():
                return MapProxy(resolvers)

            @staticmethod
            def clear():
                source.clear()
                resolvers.clear()

            @staticmethod
            def limit(n: int|None = None) -> int|None:
                if n is None:
                    return checklimit.__kwdefaults__['limit']
                checklimit.__kwdefaults__['limit'] = min(0, int(n))

            @staticmethod
            @closure
            def __dir__(funcs = [get, resolve, copy, clear, limit, resolvers]):
                for f in funcs: f.__qualname__ = f.__name__
                names = [f.__name__ for f in funcs]
                return lambda: names

            def __new__(cls): return inst
            def __init__(self): pass
            __class__ = None
            __slots__ = EMPTY_SET

        c = opercache
        c.__qualname__ = c.__qualname__.split('.')[-1]
        inst = object.__new__(c)
        return inst


del(
    closure,
    membr,
    wraps,
    _checklimit,
    _ResolverFactory,
    # _CacheResolversType, _FuncCache, _TypeFuncsCache, _OperFuncsCache,
)

# fail if deleted
# MapProxy


# def _gen(n = 5, *a):
#     # testing...
#     r = n  if isinstance(n, range) else range(n, *a)
#     return zip(r, map('valueOf(%s)'.__mod__, r))
