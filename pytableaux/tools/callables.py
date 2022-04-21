from __future__ import annotations

__all__ = (
    # 'Caller',
    # 'calls',
    # 'gets',
    # 'sets',
    # 'dels',
    # 'raiser',
    'cchain',
    #'preds',
)

import operator as opr
from functools import partial#, WRAPPER_ASSIGNMENTS
from itertools import filterfalse
from typing import (Any, Callable, Collection, Iterable, Iterator,
                    # Literal,
                    # Mapping, Sequence, TypeVar,
                    # final
                    )

from pytableaux.errors import check
from pytableaux.tools import static #, abstract, MapProxy
# from pytableaux.tools.abcs import Copyable, FlagEnum
# from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.typing import F, P, T #, RT


# class Flag(FlagEnum):

#     Blank  = 0
#     Init   = 1
#     Lock   = 2

#     Bound  = 4
#     Sliced = 8
#     Order  = 16

#     Safe   = 32
#     Left   = 64
#     Star   = 128
#     Usr1   = 256
#     User   = Safe | Star | Left | Usr1

#     Copy   = 512


# ExceptsParam = tuple[type[Exception], ...]
# FlagParam = Flag | Callable[[Flag], Flag]

EMPTY = ()
NOARG = object()

# class _objwrap(Callable):
#     'Object wrapper to allow __dict__ attributes'

#     __slots__ = 'caller', '__dict__'

#     def __init__(self, caller: Callable):
#         self.caller = caller

#     def __call__(self, *a, **kw):
#         return self.caller(*a, **kw)

# class Caller(Callable[..., RT], Copyable):

#     #: Alias members for common user flags.
#     SAFE: Literal[Flag.Safe] = Flag.Safe
#     LEFT: Literal[Flag.Left] = Flag.Left
#     STAR: Literal[Flag.Star] = Flag.Star

#     #: Class attributes.
#     cls_flag     = Flag.Blank
#     safe_errs    : ExceptsParam
#     safe_default : Any = None

#     #: Instances do not have all the possible attributes set. The
#     #: The _attrhints says that an instance will most likely have the
#     #: attribute (key) if the hint (value) is in the instance's flag.
#     #:
#     #: Hints for subclasses are automatically merged in the subclass
#     #: hook. If a subclass's instances will always have an attribute,
#     #: then including it in __slots__ is sufficient, which will be
#     #: merged with the hint value of Flag.Blank, meaning 'always present'.
#     _attrhints: Mapping[str, Flag] = dict(
#         flag     = Flag.Blank,
#         bindargs = Flag.Bound,
#         aslice   = Flag.Sliced,
#         aorder   = Flag.Order,
#         excepts  = Flag.Safe,
#         default  = Flag.Safe,
#     )
#     __slots__ = setf(_attrhints) | {'__hash'}
    
#     #: Instance Attributes.

#     flag     : Flag
#     bindargs : tuple
#     aslice   : slice
#     excepts  : ExceptsParam
#     default  : Any

#     @abstract
#     def _call(self, *args) -> RT:
#         raise NotImplementedError

#     def __new__(cls: type[CallT], *args, **kw) -> CallT:
#         inst = super().__new__(cls)
#         inst.flag = Flag.Blank | cls.cls_flag
#         return inst

#     def __init__(self, *bindargs,
#         flag: FlagParam = None,
#         aslice: slice = None,
#         aorder: tuple[int, ...] = None,
#         excepts: ExceptsParam = None,
#         default: Any = None,
#     ):
#         f = self.flag
#         if flag is not None:
#             if callable(flag): flag = flag(f)
#             # Only permit changes to user portion
#             f = (f & ~f.User) | (flag & f.User)
#         if aslice:
#             f |= f.Sliced
#             self.aslice = check.inst(aslice, slice)
#         if f.Safe in f or excepts is not None:
#             f |= f.Safe
#             self.excepts = excepts or self.safe_errs
#             if default is not None: self.default = default
#             else: self.default = self.safe_default
#         if aorder:
#             f |= f.Order
#             self.aorder = aorder
#         if bindargs:
#             f |= f.Bound
#             self.bindargs = bindargs
#         self.flag = f | f.Init | f.Lock

#     @final
#     def __call__(self, *args: Any, **kw) -> RT:
#         try: return self._call(*self.getargs(args), **kw)
#         except Exception as err:
#             if Flag.Safe in self.flag and isinstance(err, self.excepts):
#                 return self.default
#             raise

#     def getargs(self, args: Sequence) -> Sequence:
#         f = self.flag
#         if f.Star in f: args, = args
#         if f.Sliced in f: args = args[self.aslice]
#         if f.Bound in f:
#             if f.Left in f: args = self.bindargs + args
#             else: args = args + self.bindargs
#         if f.Order in f:
#             args = tuple(map(args.__getitem__, self.aorder))
#         return args

#     def attrnames(self):
#         return (name for name, hint in self._attrhints.items() if hint in self.flag)

#     def attritems(self):
#         return ((name, getattr(self, name)) for name in self.attrnames())

#     def copy(self, /, *, sa = object.__setattr__):
#         inst = object.__new__(type(self))
#         for name, value in self.attritems():
#             sa(inst, name, value)
#         return inst

#     def __setattr__(self, name, value, /, *,
#         sa = object.__setattr__,
#         ok = setf(WRAPPER_ASSIGNMENTS).__contains__
#     ):
#         try: f = self.flag
#         except AttributeError: pass
#         else:
#             if f.Lock in f and not ok(name):
#                 raise AttributeError(name, f.Lock)
#         sa(self, name, value)

#     def __delattr__(self, attr):
#         raise AttributeError(attr)

#     def __getattr__(self, attr):
#         try: f = self.flag
#         except: raise AttributeError(attr)
#         if f.Init not in f:
#             if attr == 'safe_errs':
#                 raise TypeError("'excepts' required for %s with %s" % (type(self), f.Safe))
#         raise AttributeError(attr)

#     def __eq__(self, other: CallT):
#         if self is other:
#             return True
#         if type(self) is not type(other):
#             if isinstance(other, __class__):
#                 return False
#             else:
#                 return NotImplemented
#         try:
#             for a, b in zip(
#                 self.attritems(),
#                 other.attritems(),
#                 strict = True
#             ):
#                 if a != b: return False
#         except ValueError:
#             return False
#         return True

#     def __hash__(self, /, *, sa = object.__setattr__, nf = '_{0.__name__}__hash'.format):
#         locked = Flag.Lock in self.flag
#         if locked:
#             try: return self.__hash
#             except AttributeError: pass
#             sa(self, nf(__class__), self._hash())
#             return self.__hash
#         return id(self)
    
#     def _hash(self):
#         return hash(type(self)) + hash(tuple(self.attritems()))

#     def __dir__(self):
#         return list(self.attrnames())

#     def __repr__(self):
#         from pytableaux.tools.misc import orepr
#         return orepr(self, dict(self.attritems()))

#     def __init_subclass__(subcls: type[CallT], **kw):
#         super().__init_subclass__(**kw)
#         hints = __class__._attrhints | subcls._attrhints
#         subcls._attrhints = MapProxy(hints | {
#             name: Flag.Blank for name in subcls.__slots__.difference(hints)
#         })

#     def asobj(self):
#         return _objwrap(self)

# CallT = TypeVar('CallT', bound = Caller)


# @static
# class gets:

#     class key(Caller):
#         'Subscript getter.'
#         def _call(self, obj, key): return obj[key]
#         __slots__ = EMPTY_SET
#         safe_errs = KeyError, IndexError,



# @static
# class funciter:

#     def reduce(funcs: Iterable[F], /, *args, **kw) -> Any:
#         it = iter(funcs)
#         try:
#             value = next(it)(*args, **kw)
#         except StopIteration:
#             raise TypeError('reduce() of empty iterable') from None
#         for f in it:
#             value = f(value)
#         return value

#     def consume(
#         funcs: Iterable[Callable[P, T]],
#         consumer: Callable[[Iterable[P]], T],
#         /, *args, **kw
#     ) -> T:
#         return consumer(f(*args, **kw) for f in funcs)


def func_reduce(funcs: Iterable[F], /, *args, **kw) -> Any:
    it = iter(funcs)
    try:
        value = next(it)(*args, **kw)
    except StopIteration:
        raise TypeError('reduce() of empty iterable') from None
    for f in it:
        value = f(value)
    return value

def func_consume(
    funcs: Iterable[Callable[P, T]],
    consumer: Callable[[Iterable[P]], T],
    /, *args, **kw
) -> T:
    return consumer(f(*args, **kw) for f in funcs)

@static
class cchain:

    def forall(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        'Return a reusable predicate (conjuncts).'
        return partial(func_consume, funcs, all)

    def forall_collection(funcs: Collection[Callable[P, bool]]) -> Callable[P, bool]:
        'Return a reusable predicate (conjuncts) from a single collection.'
        return partial(func_consume, check.inst(funcs, Collection), all)

    def forany(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        'Return a reusable predicate (disjuncts).'
        return partial(func_consume, funcs, any)

    def forany(funcs: Collection[Callable[P, bool]]) -> Callable[P, bool]:
        'Return a reusable predicate (disjuncts) from a single collection.'
        return partial(func_consume, check.inst(funcs, Collection), any)

    def reducer(*funcs: F) -> F:
        'Return a reusable reducer.'
        if not len(funcs):
            raise TypeError('must pass at least one argument.')
        return partial(func_reduce, funcs)

    def reduce_filter(it: Iterable[T], finit: F, /, *preds: F) -> Iterator[T]:
        'Filter immediate. NB: First argument is the iterable to filter.'
        return filter(cchain.reducer(finit, *preds), it)

    def reduce_filterfalse(it: Iterable[T], finit: F, /, *preds: F) -> Iterator[T]:
        'Filter immediate. NB: First argument is the iterable to filter.'
        return filterfalse(cchain.reducer(finit, *preds), it)

del(
    # abstract,
    # final,
    static,
    opr,
)
