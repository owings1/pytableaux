from __future__ import annotations

__all__ = (
    'MappingApi',
    'MutableMappingApi',
    'MapCover',
    'MapAttrCover',
    'dmap',
    'defaultdmap',
    'dmapattr',
    'ItemsIterator',
    'DequeCache',
    'KeyGetAttr',
    'KeySetAttr',
)

from errors import Emsg, instcheck
from tools.abcs import (
    Abc, Copyable, MapProxy, abcf, F, KT, VT #, T, P, RT
)
from tools.callables import preds, gets
from tools.decorators import (
    abstract, static, final, overload,
    fixed, membr, operd, wraps,
)

from collections.abc import (
    Collection, Iterator, Mapping, MutableMapping, Set
)
from collections import defaultdict, deque
from itertools import (
    chain, filterfalse, starmap
)
from operator import not_, truth
from typing import (
    Any, Callable, Iterable, TypeVar,
)


EMPTY = ()
EMPTY_ITER = iter(EMPTY)
FCACHE_MAXMISS = 50
FNOTIMPL = fixed.value(NotImplemented)()
FTHRU = gets.Thru

class FuncResolvers(dict[tuple[Callable, Callable], Callable]):

    __slots__ = EMPTY

    def __missing__(self, pair):
        while len(self) > FCACHE_MAXMISS and len(self) > 0:
            self.pop(next(iter(self)))
        res_create, get_res_iter = pair
        def cached_resolver(obj, other):
            return res_create(get_res_iter(obj, other))
        cached_resolver.__qualname__ = cached_resolver.__name__
        return self.setdefault(pair, cached_resolver)

class FuncCache(dict[type, Callable]):

    __slots__ = 'get_res_iter', 'get_res_type',

    def __init__(self, obj_type: type[MappingApi], oper_name: str, /):
        self.get_res_iter = getattr(obj_type, oper_name + 'op__')
        if oper_name.startswith('__r'):
            self.get_res_type = obj_type._roper_res_type
        else:
            self.get_res_type = obj_type._oper_res_type

    def __missing__(self, other_type):
        while len(self) > FCACHE_MAXMISS and len(self) > 0:
            self.pop(next(iter(self)))
        return self.setdefault(other_type, self.resolve)

    def resolve(self, obj, other, /):
        other_type = type(other)
        if not issubclass(other_type, Iterable):
            return self.reject(other_type)
        res_type = self.get_res_type(other_type)
        if res_type is NotImplemented:
            return self.reject(other_type)
        get_res_iter = self.get_res_iter
        it = get_res_iter(obj, other)
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
            return self.reject(other_type)
        else:
            raise Emsg.InstCheck(it, Iterable)
        res = res_create(it)
        self[other_type] = RESOLV_CACHE[res_create, get_res_iter]
        return res

    def reject(self, other_type):
        self[other_type] = FNOTIMPL
        return NotImplemented

class TypeFuncsCache(dict[str, FuncCache]):

    __slots__ = 'obj_type',

    def __init__(self, obj_type: type[MappingApi]):
        self.obj_type = obj_type

    def __missing__(self, oper_name: str, /, *, FuncCache = FuncCache):
        return self.setdefault(oper_name, FuncCache(self.obj_type, oper_name))

class OperFuncsCache(dict[type[Mapping], TypeFuncsCache]):

    __slots__ = EMPTY

    def __missing__(self, obj_type, TypeFuncsCache = TypeFuncsCache):
        while len(self) > FCACHE_MAXMISS and len(self) > 0:
            self.pop(next(iter(self)))
        return self.setdefault(obj_type, TypeFuncsCache(obj_type))

class MappingApi(Mapping[KT, VT], Copyable):

    __slots__ = EMPTY

    @overload
    def __or__(self:  MapiT, b: Mapping) -> MapiT: ...
    @overload
    def __ror__(self: MapiT, b: Mapping) -> MapiT: ...
    @overload
    def __ror__(self: MapiT, b: SetT) -> SetT: ...

    @overload
    def __and__(self:  MapiT, b: SetT) -> MapiT: ...
    @overload
    def __sub__(self:  MapiT, b: SetT) -> MapiT: ...

    @overload
    def __rand__(self: MapiT, b: SetT) -> SetT: ...
    @overload
    def __rsub__(self: MapiT, b: SetT) -> SetT: ...
    @overload
    def __rxor__(self: MapiT, b: SetT) -> SetT: ...


    @abcf.temp
    @membr.defer
    def oper(member: membr):
        oper_name = member.name
        @wraps(member)
        def f(self, other):
            return FCACHE_OP[type(self)][oper_name][type(other)](self, other)
        return f

    __or__ = __ror__ = __and__ = __rand__ = __sub__ = __rsub__ = __rxor__ = oper()

    def __or__op__(self, other: Mapping):
        'Mapping | Mapping -> Mapping'
        return chain(ItemsIterator(self), ItemsIterator(other))

    def __ror__op__(self, other: Mapping|Set):
        'Set     | Mapping --> Set'
        if isinstance(other, Set): return chain(other, self)
        'Mapping | Mapping --> Mapping'
        return chain(ItemsIterator(other), ItemsIterator(self))

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

    @classmethod
    def _from_mapping(cls: type[MapiT], mapping: Mapping) -> MapiT:
        'Construct a new instance from a mapping.'
        return cls(mapping)

    @classmethod
    def _from_iterable(cls: type[MapiT], it: Iterable[tuple[Any, Any]]) -> MapiT:
        'Construct a new instance from an iterable of item tuples.'
        return NotImplemented

    @classmethod
    def _oper_res_type(cls, other_type: type[Iterable]):
        '''Return the type (or callable) to construct a new instance from the result
        of an arithmetic operator expression for objects of type cls on the left hand
        side, and of other_type on the right hand side.'''
        return cls

    @classmethod
    def _roper_res_type(cls, other_type: type[Iterable]):
        '''Return the type (or callable) to construct a new instance from the result
        of an arithmetic operator expression for objects of type cls on the right hand
        side, and of other_type on the left hand side.'''
        if issubclass(other_type, Set):
            return other_type
        return cls._oper_res_type(other_type)

class KeyGetAttr(MappingApi[Any, VT]):
    'Mixin class for attribute key access.'

    # TODO: this is slow

    __slots__ = EMPTY

    def __getattr__(self, name) -> VT:
        try:
            return self[name]
        except KeyError:
            pass
        return super().__getattr__(name)

    def __dir__(self):
        return list(filter(preds.isattrstr, self))

class MapCover(MappingApi[KT, VT]):
    'Mapping reference.'

    __slots__ = '__len__', '__getitem__', '__iter__', '__reversed__'

    def __init__(self, mapping: Mapping[KT, VT] = None, /, **kwmap):
        if mapping is None: mapping = kwmap
        else:
            instcheck(mapping, Mapping)
            if len(kwmap):
                raise TypeError('Expected mapping or kwargs, not both.')
        self._init_cover(mapping, self)

    @static
    def _init_cover(src, dest, /, *,
        names = __slots__, ga = object.__getattribute__, sa = object.__setattr__
    ):
        for name in names:
            sa(dest, name, ga(src, name))

    __slots__ = frozenset(__slots__)

    def __delattr__(self, name, /, *, slots = __slots__):
        if name in slots:
            raise Emsg.ReadOnlyAttr(name, self)
        super().__delattr__(name)

    def __setattr__(self, name, value, /, *, slots = __slots__):
        if name in slots:
            raise Emsg.ReadOnlyAttr(name, self)
        super().__setattr__(name, value)

    def __repr__(self):
        return repr(dict(self))

    @classmethod
    def _from_iterable(cls, it):
        return cls._from_mapping(dict(it))

class MapAttrCover(MapCover[KT, VT], KeyGetAttr[VT]):
    'MapCover + KeyGetAttr'
    __slots__ = EMPTY
    # TODO: this is slow

class MutableMappingApi(MappingApi[KT, VT], MutableMapping[KT, VT], Copyable):

    __slots__ = EMPTY

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

    def _setitem_update(self, it = EMPTY_ITER, /, **kw):
        '''Alternate implementation for classes that need more control'''
        it = ItemsIterator(it)
        if len(kw): it = chain(it, ItemsIterator(kw))
        for _ in starmap(self.__setitem__, it): pass

    @classmethod
    def _from_iterable(cls, it):
        return cls(it)

class dmap(dict[KT, VT], MutableMappingApi[KT, VT]):
    'Mutable mapping api from dict.'

    __slots__ = EMPTY

    copy    = MutableMappingApi.copy
    __or__  = MutableMappingApi.__or__
    __ror__ = MutableMappingApi.__ror__

class defaultdmap(defaultdict[KT, VT], MutableMappingApi[KT, VT]):
    'Mutable mapping api from defaultdict.'

    __slots__ = EMPTY

    copy    = MutableMappingApi.copy
    __or__  = MutableMappingApi.__or__
    __ror__ = MutableMappingApi.__ror__

    @classmethod
    def _from_mapping(cls, mapping):
        if isinstance(mapping, defaultdict):
            return cls(mapping.default_factory, mapping)
        return cls(None, mapping)

    @classmethod
    def _from_iterable(cls, it):
        return cls(None, it)

    @classmethod
    def _roper_res_type(cls, other_type):
        if issubclass(other_type, Mapping):
            return dmap
        return super()._roper_res_type(other_type)

class KeySetAttr(Abc):

    __slots__ = EMPTY

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if preds.isattrstr(key) and self._keyattr_ok(key):
            super().__setattr__(key, value)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self._keyattr_ok(name):
            super().__setitem__(name, value)

    def __delitem__(self, key):
        super().__delitem__(key)
        if preds.isattrstr(key) and self._keyattr_ok(key):
            super().__delattr__(key)

    def __delattr__(self, name):
        super().__delattr__(name)
        if self._keyattr_ok(name) and name in self:
            super().__delitem__(name)

    update = MutableMappingApi._setitem_update

    @classmethod
    def _keyattr_ok(cls, name):
        'Return whether it is ok to set the attribute name.'
        return not hasattr(cls, name)

class dmapattr(KeySetAttr, dmap[KT, VT]):
    __slots__ = EMPTY

class DequeCache(Collection[VT], Abc):

    __slots__ = EMPTY

    maxlen: int
    idx: int
    rev: Mapping[Any, VT]

    @abstract
    def clear(self): ...

    @abstract
    def __len__(self): ...

    @abstract
    def __getitem__(self, key) -> VT: ...

    @abstract
    def __reversed__(self) -> Iterator[VT]: ...

    @abstract
    def __setitem__(self, key, item: VT): ...

    def __new__(cls, Vtype: type, maxlen = 10):

        from errors import notsubclscheck
        notsubclscheck(Vtype, (int, slice))
        instcheck(Vtype, type)

        idx      : dict[Any, VT] = {}
        idxproxy : Mapping[Any, VT] = MapProxy(idx)

        rev      : dict[VT, set] = {}
        revproxy : Mapping[VT, set] = MapProxy(rev)

        deck     : deque[VT] = deque(maxlen = maxlen)

        class Api(DequeCache[VT]):

            __slots__ = EMPTY

            maxlen = property(lambda _: deck.maxlen)
            idx = property(lambda _: idxproxy)
            rev = property(lambda _: revproxy)

            def clear(self):
                for d in (idx, rev, deck): d.clear()

            def __len__(self):
                return len(deck)

            def __iter__(self) -> Iterator[VT]:
                return iter(deck)

            def __reversed__(self) -> Iterator[VT]:
                return reversed(deck)

            def __contains__(self, item: VT):
                return item in rev

            def __getitem__(self, key) -> VT:
                return idx[key]

            def __setitem__(self, key, item: VT):
                instcheck(item, Vtype)
                if item in self:
                    item = self[item]
                else:
                    if len(deck) == deck.maxlen:
                        old = deck.popleft()
                        for k in rev.pop(old): del(idx[k])
                    idx[item] = item
                    rev[item] = {item}
                    deck.append(item)
                idx[key] = item
                rev[item].add(key)

            __new__  = object.__new__

        Api.__qualname__ = 'DequeCache.Api'
        return Api()

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
        kpred: F = preds.true,
        vpred: F = preds.true,
        koper: F = truth,
        voper: F = truth,
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

    @static
    def _gen1(getkeys, vget, kpred, vpred, koper, voper):
        for k in getkeys():
            if koper(kpred(k)):
                v = vget(k)
                if voper(vpred(v)):
                    yield k, v

    @static
    def _gen2(items, kpred, vpred, koper, voper):
        for k, v in items:
            if koper(kpred(k)) and voper(vpred(v)):
                yield k, v


RESOLV_CACHE = FuncResolvers()
FCACHE_OP = OperFuncsCache()

MapiT = TypeVar('MapiT', bound = Mapping)
SetT  = TypeVar('SetT',  bound = Set)

del(
    abstract, static, final, overload, fixed, membr, wraps,
    FuncResolvers, FuncCache, TypeFuncsCache, OperFuncsCache,
)


def _gen(n = 5, *a):
    # testing...
    r = n  if isinstance(n, range) else range(n, *a)
    return zip(r, map('valueOf(%s)'.__mod__, r))
