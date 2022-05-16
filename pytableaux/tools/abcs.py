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
pytableaux.tools.abcs
^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import abc as _abc
import enum as _enum
import functools
import itertools
import operator as opr
from collections.abc import Set
from enum import auto as eauto
from typing import (TYPE_CHECKING, Any, Callable, Collection, Hashable,
                    Iterable, Iterator, Mapping, Sequence, SupportsIndex, TypeVar)

from pytableaux import __docformat__, tools
from pytableaux.errors import Emsg, check
from pytableaux.tools import MapProxy
from pytableaux.tools.typing import RT, TT, EnumDictType, F, T

EnumT = TypeVar('EnumT', bound = _enum.Enum)
"Bound to ``Enum``"

if TYPE_CHECKING:
    from typing import overload

    from pytableaux.tools.hooks import hookutil
    from pytableaux.tools.typing import iter
                                     

__all__ = (
    'Abc',
    'abcf',
    'AbcMeta',
    'Astr',
    'Copyable',
    'eauto',
    'Ebc',
    'EbcMeta',
    'EnumLookup',
    'Eset',
    'FlagEnum',
    'IntEnum',
    'IntFlag',
)

EMPTY = ()
NOARG = object()


def is_enumcls(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, _enum.Enum)

def em_mixins(Class: type[_enum.Enum]) -> tuple[type, ...]:
    return *itertools.filterfalse(is_enumcls, Class.__bases__),

class Eset(frozenset, _enum.Enum):
    'Enum meta enumeration.'

    Empty = frozenset()

    member_key_methods = {'_member_keys'}

    reserve_names = {'_seq', '_lookup', 'get',}

    hook_methods  = {'_member_keys', '_on_init', '_after_init'}

    clean_methods = hook_methods.copy()

def _em_fix_name_value(Class: type[EnumT], /) -> type[EnumT]:

    # cache attribute for flag enum.
    if callable(getattr(Class, '__invert__', None)):
        Class._invert_ = None # type: ignore

    # Clear DynCa from class layout
    Class.name  = None # type: ignore
    Class.value = None # type: ignore

    # Assign name & value directly.
    for member in Class:
        member.name = member._name_
        member.value = member._value_
    
    # Compatible as decorator.
    return Class

def _em_clean_methods(Class: type[EnumT], /, *,
    deleter: Callable[[type, str], Any] = type.__delattr__
) -> type[EnumT]:
    for hname in filter(Class.__dict__.__contains__, Eset.clean_methods):
        deleter(Class, hname)
    return Class

def _em_rebase(oldcls: type[EnumT], *bases: type, ns: Mapping = None, metaclass: type = None, **kw) -> type[EnumT]:
    'Rebase an enum class with the same member data.'
    # Get metaclass.
    if metaclass is None:
        # Try the metaclass of the last enum class in the new bases.
        it = filter(is_enumcls, reversed(bases))
        try:
            metaclass = type(next(it))
        except StopIteration:
            # Fall back on the old metaclass.
            metaclass = type(oldcls)
    # Validate metaclass.
    metaclass = check.subcls(check.inst(metaclass, type), _enum.EnumMeta)
    # New bases.
    if not len(bases):
        # If no new bases passed, try the last enum class of the old bases.
        it = filter(is_enumcls, reversed(oldcls.__bases__))
        bases = tuple(itertools.islice(it, 1))
        if not len(bases):
            # Fall back on built-in Enum.
            bases = (_enum.Enum,)
    # Reuse old non-enum bases.
    bases = em_mixins(oldcls) + bases
    # Class name.
    clsname = oldcls.__name__
    # Prepare class dict.
    cdict = metaclass.__prepare__(clsname, bases, **kw)
    # Add member data from old class. Use _member_map_ to include aliases.
    for mname, m in oldcls._member_map_.items():
        # Use __setitem__, not update, else EnumDict won't work.
        cdict[mname] = m._value_
    if ns is not None:
        cdict.update(ns)
    # Create class.
    return metaclass(clsname, bases, cdict, **kw)

class EnumLookup(Mapping[Any, T]):
    'Enum member lookup index.'

    if TYPE_CHECKING:
        @overload
        def build(self): ...

        @overload
        def pseudo(self, member: T, /) -> T: ...

        @overload
        def __getitem__(self, key: Any, /) -> T: ...

    _mapping: Mapping[Any, T]

    build: Callable[[], None]
    "Build and update the whole index."

    pseudo: Callable[[T], T]
    "Add a single pseudo member to the index."

    __slots__ = (
        '__getitem__',
        '_mapping',
        'build',
        'pseudo',
    )

    def __init__(self, Owner: type[T], /, build: bool = False,
        _sa = object.__setattr__
    ):

        if hasattr(self, '__getitem__'):
            raise TypeError

        source = {}

        _sa(self, '__getitem__', source.__getitem__)
        _sa(self, '_mapping', MapProxy(source))

        def _pseudo(member: EnumT) -> EnumT:
            for key in self._check_pseudo(member, Owner):
                source[key] = member
            return member

        def _build():
            source.clear()
            if len(Owner):
                builder = self._makemap(Owner, self._get_keyfuncs(Owner))
                source.update(builder)
            return self

        _sa(self, 'build', _build)
        _sa(self, 'pseudo', _pseudo)

        if build:
            _build()

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __reversed__(self):
        return reversed(self._mapping)

    def _asdict(self) -> dict[Any, T]:
        # Compatibility for JSON serialization.
        return dict(self)

    def __setattr__(self, name, value):
        raise Emsg.ReadOnly(self, name)

    def __delattr__(self, name):
        raise Emsg.ReadOnly(self, name)

    def __repr__(self):
        return repr(self._asdict())

    @classmethod
    def _makemap(cls, Owner: type[EnumT], keyfuncs: Collection[Callable], /) -> dict[Hashable, EnumT]:
        "Build an index source dictionary."

        # Named members, including aliases, but not pseudos.
        member_map = Owner._member_map_
        # Canonical names, no aliases.
        canon_names = Owner._member_names_
        # Unique members, including unnamed (pseudos), but not aliases.
        unique_members = set(Owner._value2member_map_.values())

        # Canonical members, named, unique, and ordered.
        member_seq = tuple(map(member_map.get, canon_names))
        # Unnamed (pseudo) members.
        pseudos = unique_members.difference(member_map.values())
        # Alias names
        aliases = set(member_map).difference(canon_names)

        builder = cls._seqmap(member_seq, keyfuncs)

        if len(pseudos):
            builder |= cls._pseudomap(pseudos)
        if len(aliases):
            builder |= {alias: member_map[alias] for alias in aliases}

        return builder

    @classmethod
    def _seqmap(cls,
        members: Sequence[EnumT], keyfuncs: Collection[Callable], /) -> dict[Hashable, EnumT]:
        """Build the main index map for the sequence of proper (named) members
        with the given keys functions.
        """
        return {
            key : member
            for member_keys, member in zip(
                ({key for func in keyfuncs for key in func(member)}
                    for member in members),
                members
            ) for key in member_keys
        }

    @classmethod
    def _pseudomap(cls, pseudos: Collection[EnumT], /) -> dict[Hashable, EnumT]:
        """Build a restricted index map for pseudo (unnamed) members, e.g.
        dynamic bit flag values. Only value and instance keys are used.
        """
        getkeys = cls._pseudo_keys
        return {key: entry
            for pseudo_keys, entry in (
                (getkeys(pseudo), pseudo)
                for pseudo in pseudos
            ) for key in pseudo_keys
        }

    @classmethod
    def _check_pseudo(cls, pseudo: _enum.Enum, Owner: type[_enum.Enum], /) -> set[Hashable]:
        "Verify a pseudo member, returning index keys."
        check = Owner._value2member_map_[pseudo._value_]
        if check is not pseudo:
            raise TypeError from Emsg.ValueConflict(pseudo, check)
        if pseudo._name_ is not None:
            raise TypeError from Emsg.WrongValue(pseudo._name_, None)
        return cls._pseudo_keys(pseudo)

    @classmethod
    def _get_keyfuncs(cls, Owner: type[_enum.Enum], /) -> set[Callable]:
        "Get the key functions."
        funcs = {cls._default_keys}
        for meth in Eset.member_key_methods:
            if callable(func := getattr(Owner, meth, None)):
                funcs.add(func)
        return funcs

    @staticmethod
    def _pseudo_keys(pseudo: _enum.Enum, /) -> set[Hashable]:
        'Pseudo member lookup keys'
        return {pseudo, pseudo._value_}

    @staticmethod
    def _default_keys(member: _enum.Enum, /) -> set[Hashable]:
        'Default member lookup keys'
        return {member._name_, (member._name_,), member, member._value_}


#=============================================================================
#_____________________________________________________________________________
#
#       Enum Meta
#_____________________________________________________________________________

class EbcMeta(_enum.EnumMeta):
    'General-purpose base Metaclass for all Enum classes.'

    _mixin_bases_: tuple[type, ...]
    _lookup: EnumLookup
    _seq: Sequence

    _member_names_: Sequence[str] # Use tuple instead of list
    __members__: Mapping = None # Override to not double-proxy

    @classmethod
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw) -> EnumDictType:
        return super().__prepare__(clsname, bases, **kw)

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: EnumDictType, /, *,
        skipflags: bool = False, idxbuild: bool = True, skipabcm: bool = False, **kw
    ):
        if not skipabcm:
            # Run generic Abc init hooks.
            nsinit(ns, bases, skipflags = skipflags)

        forbid = Eset.reserve_names.intersection(ns)
        if forbid:
            raise TypeError(f'Restricted names: {forbid}')

        # Create class.
        Class = super().__new__(cls, clsname, bases, ns, **kw)

        # Store mixin bases
        Class._mixin_bases_ = em_mixins(Class)

        if not skipabcm:
            # Run generic Abc after hooks.
            clsafter(Class, ns, skipflags = skipflags)

        # Freeze Enum class attributes.
        Class._member_map_ = Class.__members__ = MapProxy(Class._member_map_)
        Class._member_names_ = tuple(Class._member_names_)

        # Create lookup index.
        Class._lookup = EnumLookup(Class)

        if not len(Class):
            # No members to process.
            Class._seq = EMPTY
            Class._after_init()
            return Class

        # Store the fixed member sequence. Necessary for iterating.
        Class._seq = tuple(
            map(Class._member_map_.__getitem__, Class._member_names_)
        )

        # Performance tweaks.
        _em_fix_name_value(Class)

        # Init hook to process members before index is created.
        Class._on_init(Class)

        # Build index, if applicable.
        if idxbuild:
            Class._lookup.build()

        # After init hook.
        Class._after_init()

        # Cleanup.
        _em_clean_methods(Class)

        return Class

    #******  Class Call

    def __call__(cls, value, names = None, **kw):
        if names is not None:
            return super().__call__(value, names, **kw)
        try:
            return cls._lookup[value]
        except KeyError:
            pass
        # It must be a pseudo member, since it was not in _lookup.
        return cls._lookup.pseudo(
            # Will raise ValueError for bad value.
            cls.__new__(cls, value)
        )

    #******  Mapping(ish) Behavior

    def get(cls, key, default = NOARG, /):
        """Get a member by an indexed reference key.

        Args:
            key: member lookup key, value, instance, etc..
            default: value to return if not found.

        Returns:
            The enum member, or default if specified and not found.

        Raises:
            KeyError: if not found and no default specified.
        """
        try:
            return cls._lookup[key]
        except KeyError:
            if default is NOARG:
                raise
            return default

    def __getitem__(cls, key, /):
        return cls._lookup[key]

    def __contains__(cls, key: Any, /):
        return key in cls._lookup

    #******  Sequence(ish) Behavior

    def __iter__(cls):
        return iter(cls._seq)

    def __reversed__(cls):
        return reversed(cls._seq)

    #******  Misc Behaviors

    def __getattr__(cls, name, /):
        raise AttributeError(name)

    def __dir__(cls):
        return cls._member_names_

    #******  Subclass Init Hooks

    def _member_keys(cls, member: Any, /) -> Set[Hashable]:
        'Init hook to get the index lookup keys for a member.'
        return Eset.Empty

    def _on_init(cls, subcls: type, /):
        '''Init hook after all members have been initialized, before index
        is created. **NB:** Skips abstract classes.'''
        pass

    def _after_init(cls):
        'Init hook once the class is initialized. Includes abstract classes.'
        pass

    if TYPE_CHECKING:

        @overload
        def __call__(cls: EbcMeta|type[EnumT], value: Any, /) -> EnumT: ...
        @overload
        def __call__(cls: EbcMeta|type[EnumT], value: Any, names: Any, /, **kw) -> type[EnumT]: ...

        @overload
        def __getitem__(cls: EbcMeta|type[EnumT], key: Any, /) -> EnumT: ...

        @overload
        def get(cls: EbcMeta|type[EnumT], key: Any, /) -> EnumT: ...
        @overload
        def get(cls: EbcMeta|type[EnumT], key: Any, default: T, /) -> EnumT|T: ...

        @overload
        def __iter__(cls: EbcMeta|type[EnumT]) -> Iterator[EnumT]: ...
        @overload
        def __reversed__(cls: EbcMeta|type[EnumT]) -> Iterator[EnumT]: ...

        @property
        @overload
        def _seq(cls: EbcMeta|type[EnumT]) -> Sequence[EnumT]: ...

        @property
        @overload
        def _lookup(cls: EbcMeta|type[EnumT]) -> EnumLookup[EnumT]: ...

        @property
        @overload
        def _member_map_(cls: EbcMeta|type[EnumT]) -> Mapping[str, EnumT]: ...

        @property
        @overload
        def __members__(cls: EbcMeta|type[EnumT]) -> Mapping[str, EnumT]: ...

#=============================================================================
#_____________________________________________________________________________
#
#       Ebc Support Classes
#
#           skipflags = True
#           skipabcm = True
#_____________________________________________________________________________

class Ebc(_enum.Enum, metaclass = EbcMeta, skipflags = True, skipabcm = True):

    __slots__ = Eset.Empty

    name  : str
    value : Any

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    @classmethod
    def _on_init(cls, subcls: type):
        'Propagate hook up to metaclass.'
        EbcMeta._on_init(cls, subcls)

    @classmethod
    def _member_keys(cls, member: Any) -> Set[Hashable]:
        'Propagate hook up to metaclass.'
        return EbcMeta._member_keys(cls, member)

    @classmethod
    def _after_init(cls):
        'Propagate hook up to metaclass.'
        EbcMeta._after_init(cls)

    def __repr__(self):
        clsname = type(self).__name__
        mixins = getattr(self, '_mixin_bases_', None)
        try:
            s = f'{clsname}.{self._name_}'
            if mixins:
                mfn = mixins[0].__repr__
                return f'<{s}:{mfn(self._value_)}>'
            return f'<{s}>'
        except AttributeError:
            return f'<{clsname}.?ERR?>'

class Astr(str, Ebc, skipflags = True, skipabcm = True):
    "Attribute names for abc functionality."

    flag     = '_abc_flag'
    hookuser = '_abc_hook_user'
    hookinfo = '_abc_hook_info'

class FlagEnum(_enum.Flag, Ebc, skipflags = True, skipabcm = True):

    name  : str|None
    value : int

    _invert_ : tuple[int, FlagEnum]

    @classmethod
    def _missing_(cls, value: Any, /):
        member: FlagEnum = super()._missing_(value)
        member.value = member._value_
        member.name  = member._name_
        return member

    def __invert__(self):
        cached = self._invert_
        value = self.value
        if cached is not None and cached[0] == value:
            return cached[1]
        other = super().__invert__()
        self._invert_ = value, other
        other._invert_ = other.value, self
        return other

class abcf(FlagEnum, skipflags = True, skipabcm = True):
    'Enum flag for AbcMeta functionality.'

    __slots__ = 'name', 'value', '_value_', '_invert_'

    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32
    inherit = 64

    _cleanable = before | temp | after

    def __call__(self, obj: F) -> F:
        """Add the flag to obj's meta flag with bitwise OR. Return obj for
        decorator use.
        """
        return self.save(obj, self | self.read(obj))

    @classmethod
    def read(cls, obj, default: abcf|int = 0, /, *, attr: str = Astr.flag) -> abcf:
        "Get the flag (or `blank`) for any obj."
        return getattr(obj, attr, cls(default))

    @classmethod
    def save(cls, obj: F, value: abcf|int, /, *, attr: str = Astr.flag) -> F:
        'Write the value, returns obj for decorator use.'
        setattr(obj, attr, cls(value))
        return obj

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Meta
#_____________________________________________________________________________

def nsinit(ns: dict, bases: tuple[type, ...], /, skipflags: bool = False) -> None:
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

def clsafter(Class: TT, ns: Mapping = None, /, skipflags: bool = False,
    deleter: Callable[[type, str], Any] = type.__delattr__) -> TT:
    'After class init routine. Usable as standalone class decorator.'
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

def isabstract(obj) -> bool:
    "Whether a class or method is abstract."
    if isinstance(obj, type):
        return bool(len(getattr(obj, '__abstractmethods__', Eset.Empty)))
    return bool(getattr(obj, '__isabstractmethod__', False))

def annotated_attrs(obj) -> dict[str, tuple]:
    'Evaluate annotions of type :obj:`typing.Annotated`.'
    # This is called infrequently, so we import lazily.
    from typing import Annotated, get_args, get_origin, get_type_hints
    hints = get_type_hints(obj, include_extras = True)
    return {
        k: get_args(v) for k,v in hints.items()
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
        else:
            return NotImplemented
    return True

def merge_attr(obj, name: str, it = None, /, *,
    setter: Callable[[type, str, Any], Any] = setattr, **kw
):
    """Merge an object's attribute, either from objects, or an mro.

    Args:
        obj: The object to update.
    
    Keyword Args:
        setter (Callable): The function to set the attribute, default
            is :obj:`setattr`.
        
    .. note:: Additional arguments are passed to :attr:`merged_attr`.

    """
    if it is None:
        check.inst(kw.setdefault('cls', obj), type)
    value = merged_attr(name, it, **kw)
    setter(obj, name, value)
    return value

def merged_attr(name: str, it: Iterable = None, /, *,
    oper: Callable[[Any, Any], RT] = opr.or_,
    initial:RT|Any = NOARG,
    default:RT|Any = NOARG,
    transform: Callable[[Any], RT] = tools.thru,
    getitem: bool = False,
    **iteropts
) -> RT:
    """Get merged attribute value, either from objects, or an mro.

    Args:
        name: The attribute/key name.
        it: The iterable of objects. If ``None``, :attr:`mroiter` is
            called with `**iteropts`.

    Keyword Args:
        oper (Callable): The reduce operator, default is :obj:`operator.or_`.
        initial (Any): The initial reduce value. From :func:`functools.reduce`:
            If initial is present, it is placed before the items of the
            iterable in the calculation, and serves as a default when
            the iterable is empty.
        default (Any): The default value for each object in the iterable.
            If not present, `initial` is used if present.
        transform (Callable): A type or callable to transform the final value.
        getitem (bool): Whether to use subscript instead of :obj:`getattr`.

    Returns:
        The merged value.                
    """
    if it is None:
        # check.inst(cls, type)
        it = mroiter(**iteropts)
    elif iteropts:
        raise TypeError(f'Unexpected kwargs: {list(iteropts)}')
    if getitem:
        getter = tools.getitem
    else:
        getter = getattr
    if default is NOARG:
        it = (getter(c, name) for c in it)
    else:
        it = (getter(c, name, default) for c in it)
        if initial is NOARG:
            initial = default
    if initial is NOARG:
        value = functools.reduce(oper, it)
    else:
        value = functools.reduce(oper, it, initial)
    return transform(value)

def mroiter(cls: type, *,
    supcls: type[T]|tuple[type, ...] = None,
    mcls: type|tuple[type, ...] = None,
    reverse: bool = True,
    start: SupportsIndex = None,
    stop: SupportsIndex = None,
) -> Iterator[type[T]]:
    """Returns an iterator for a class's mro with filters.

    Args:
        cls: The base class.

    Keyword Args:
        supcls (type): The class(es) of which members must be a subclass.
        mcls (type): The metaclass(es) of which members must be an instance.
        reverse (bool): Start from the top with :obj:`object`. Default ``True``.
        start (int): An index from which to start.
        stop (int): An index at which to stop.
    
    Returns:
        An iterator.
    """
    it = cls.mro()
    if reverse:
        it = reversed(it)
    else:
        it = iter(it)
    if mcls is not None:
        it = filter(lambda c: isinstance(c, mcls), it)
    if supcls is not None:
        it = filter(lambda c: issubclass(c, supcls), it)
    if start is not None or stop is not None:
        it = itertools.islice(it, start, stop) # type: ignore
    return it

@staticmethod
def hookable(*hooks: str, attr = Astr.hookinfo):
    'Decorator factory for specifying available hooks (provider).'
    def decorator(func: F) -> F:
        value = getattr(func, attr, None)
        if value is None:
            value = set()
            setattr(func, attr, value)
        value.update(hooks)
        return func
    return decorator

class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, /, *,
        hooks: Mapping = None,
        skiphooks: bool = False,
        skipflags: bool = False,
        hookinfo: Mapping = None,
        **kw
    ):
        nsinit(ns, bases, skipflags = skipflags)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        if not skiphooks:
            hookutil.init_user(Class, hooks)
        clsafter(Class, ns, skipflags = skipflags)
        if not skiphooks:
            hookutil.init_provider(Class, hookinfo)
        return Class

    def hook(cls, *hooks: str, attr: str = Astr.hookuser) -> Callable[[F], F]:
        'Decorator factory for tagging hook implementation (user).'
        def decorator(func: F) -> F:
            value = getattr(func, attr, None)
            if value is None:
                value = {}
                setattr(func, attr, value)
            impl = value.setdefault(cls, {})
            for name in hooks:
                if name in impl:
                    raise TypeError from Emsg.DuplicateKey(name)
                impl[name] = func
            return func
        return decorator

#=============================================================================
#_____________________________________________________________________________
#
#       Abc Base Classes
#
#           skiphooks = True
#_____________________________________________________________________________

class Abc(metaclass = AbcMeta, skiphooks = True):
    'Convenience for using AbcMeta as metaclass.'

    __slots__ = Eset.Empty

class Copyable(metaclass = AbcMeta, skiphooks = True):

    __slots__ = Eset.Empty

    @tools.abstract
    def copy(self):
        cls = type(self)
        return cls.__new__(cls)

    __copy__ = copy

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return check_mrodict(subcls.mro(), '__copy__', 'copy')

    def __init_subclass__(subcls: type[Copyable], immutcopy: bool = False, **kw):
        "Subclass init hook. Set `__copy__()` to `copy()`."
        super().__init_subclass__(**kw)
        if immutcopy:
            if 'copy' not in subcls.__dict__:
                subcls.copy = Ebc.__copy__
            if '__deepcopy__' not in subcls.__dict__:
                subcls.__deepcopy__ = Ebc.__deepcopy__
        subcls.__copy__ = subcls.copy

#=============================================================================
#_____________________________________________________________________________
#
#       Enum Base Classes
#_____________________________________________________________________________

class IntEnum(int, Ebc):
    __slots__ = Eset.Empty
    # NB: "nonempty __slots__ not supported for subtype of 'IntEnum'"
    pass

class IntFlag(int, FlagEnum):
    __slots__ = Eset.Empty
    # NB: slots must be empty for int (layout conflict)
    pass

#=============================================================================
#_____________________________________________________________________________
#
#       Rebases
#_____________________________________________________________________________

from pytableaux import errors

Eset = _em_rebase(Eset, Ebc)
Emsg = errors.Emsg = _em_rebase(Emsg, errors.EmsgBase, Ebc)

del(
    errors.EmsgBase,
    _abc,
    opr,
)
