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
pytableaux.lang
---------------

"""
from __future__ import annotations

import enum as _enum
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Iterable, Mapping,
                    NamedTuple, Set)

from pytableaux.errors import Emsg
from pytableaux.tools import EMPTY_MAP, MapProxy, abcs, closure, dxopy
from pytableaux.tools.decorators import NoSetAttr, raisr
from pytableaux.tools.sets import EMPTY_SET, setm
from pytableaux.tools.typing import CrdT, LexAbcT, LexT, T, TbsT

if TYPE_CHECKING:
    from typing import Iterator, Sequence, overload

    from pytableaux.lang.lex import (Lexical, LexType, Predicate, Quantifier,
                                     Sentence, Variable)
    from pytableaux.lang.parsing import Parser
    from pytableaux.lang.writing import LexWriter
    from pytableaux.tools.abcs import EnumLookup

__all__ = (
    # Classes
    'BiCoords',
    'LangCommonEnum',
    'LangCommonEnumMeta',
    'LangCommonMeta',
    'LexicalAbcMeta',
    'Marking',
    'Notation',
    'RenderSet',
    'SysPredEnumMeta',
    'TableStore',
    'TriCoords',

    # Attributes
    'nosetattr',
    'raiseae',

    # Type aliases
    'PredicateSpec',
    'ParameterSpec',
    'AtomicSpec',

    # Generic aliases
    'IdentType',
    'OperandsSpec',
    'OperatedSpec',
    'OperatorSpec',
    'ParameterIdent',
    'PredicatedSpec',
    'PredicateRef',
    'QuantifiedSpec',
    'QuantifierSpec',
    'SpecType',

    # Deferred aliases
    'OperCallArg',
    'ParseTableKey',
    'ParseTableValue',
    'PredsItemRef',
    'PredsItemSpec',
    'QuantifiedItem',

    # Type variables
    'CrdT',
    'LexAbcT',
    'LexT',
    'TbsT',

    # Subpackage convenience import
    'Atomic',
    'Constant',
    'LexType',
    'LexWriter',
    'Operated',
    'Operator',
    'Parser',
    'ParseTable',
    'Predicate',
    'Predicated',
    'Quantified',
    'Quantifier',
    'Variable',
)

nosetattr = NoSetAttr(attr = '_readonly', enabled = False)
raiseae = raisr(AttributeError)

#==========================+
#  Meta classes            |
#==========================+

class LangCommonMeta(abcs.AbcMeta):
    "Common metaclass for lang classes."
    
    # The nosetattr member is shared among these classes and is activated after
    # the modules are fully initialized.

    _readonly : bool
    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.AbcMeta)

class LangCommonEnumMeta(abcs.EbcMeta):
    'Common Enum metaclass for lang classes.'

    _readonly : bool
    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.EbcMeta)

class LexicalAbcMeta(LangCommonMeta):
    "Common metaclass for non-Enum lexical classes."

    # Populated in lex module.
    __call__ = NotImplemented

class SysPredEnumMeta(LangCommonEnumMeta):
    "Meta class for special system predicates enum."

    if TYPE_CHECKING:

        __members__: Mapping[str, Predicate]
        _lookup: EnumLookup[Predicate]
        _member_map_: Mapping[str, Predicate]
        _seq: Sequence[Predicate]

        @overload
        def __iter__(cls) -> Iterator[Predicate]: ...
        @overload
        def __reversed__(cls) -> Iterator[Predicate]: ...
        @overload
        def __getitem__(cls, key, /) -> Predicate: ...
        @overload
        def __call__(cls, value, /) -> Predicate: ...
        @overload
        def get(cls, key, /) -> Predicate: ...
        @overload
        def get(cls, key, default: T, /) -> Predicate|T: ...

#==========================+
#  Base classes            |
#==========================+

class LangCommonEnum(abcs.Ebc, metaclass = LangCommonEnumMeta):
    'Common Enum base class for lang classes.'

    __slots__   = 'value', '_value_', '_name_', '__objclass__'

    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.Ebc, cls = True)

#==========================+
#  Enum classes            |
#==========================+

class Notation(LangCommonEnum):
    'Notation (polish/standard) enum class.'

    default: ClassVar[Notation]
    "The default notation."

    @abcs.abcf.after
    def _(cls): cls.default = cls.polish

    charsets: setm[str]
    "All render charsets for the notation's writer classes."

    default_charset: str
    "The render charset of the notation's default writer."

    writers: setm[type[LexWriter]]
    "All writer classes for the notation."

    DefaultWriter: type[LexWriter]
    "The notations's default writer class."

    rendersets: setm[RenderSet]
    "All RenderSets of the notation."

    Parser: type[Parser]
    "The notation's parser class."

    #--- Members

    polish = abcs.eauto(), 'unicode'
    "Polish notation."

    standard = abcs.eauto(), 'unicode'
    "Standard notation."

    def __init__(self, num, default_charset: str, /):
        self.charsets = setm((default_charset,))
        self.default_charset = default_charset
        self.writers = setm()
        self.DefaultWriter = None
        self.rendersets = setm()

    __slots__ = (
        'charsets',
        'default_charset',
        'DefaultWriter',
        'Parser',
        'rendersets',
        'writers',
    )

    @classmethod
    def get_common_charsets(cls):
        "Get charsets common to all notations."
        charsets: set[str] = set(
            charset
            for notn in Notation
                for charset in notn.charsets
        )
        for notn in Notation:
            charsets = charsets.intersection(notn.charsets)
        return sorted(charsets)

    @closure
    def __setattr__():
        from enum import Enum
        esa = Enum.__setattr__
        def setter(self, name: str, value):
            if name == 'Parser' and not hasattr(self, name):
                esa(self, name, value)
            else:
                super().__setattr__(name, value)
        return setter

class Marking(LangCommonEnum):
    'Miscellaneous marking/punctuation enum.'

    paren_open = abcs.eauto()
    "Open parenthesis marking."

    paren_close = abcs.eauto()
    "Close parenthesis marking."

    whitespace = abcs.eauto()
    "Whitespace marking."

    digit = abcs.eauto()
    "Digit marking."

    meta = abcs.eauto()
    "Meta marking."

    subscript = abcs.eauto()
    "Subscript marking."

#==========================+
#  Aux classes             |
#==========================+

class BiCoords(NamedTuple):
    "An (`index`, `subscript`) integer tuple."

    index: int
    "The index integer."

    subscript: int
    "The subscript integer."

    class Sorting(NamedTuple):
        "BiCoords sorting tuple (`subscript`, `index`)."

        subscript: int
        "The subscript integer."

        index: int
        "The index integer."

    def sorting(self) -> BiCoords.Sorting:
        "Return the sorting tuple."
        return self.Sorting(self.subscript, self.index)

    first = (0, 0)

    def __repr__(self):
        return repr(tuple(self))

    @staticmethod
    def min_unused(used: Set[BiCoords], maxi: int):
        # finds the mimimum available by searching for gaps.
        if not used:
            return BiCoords.first
        index = sub = 0
        while (index, sub) in used:
            index += 1
            if index > maxi:
                index, sub = 0, sub + 1
        return BiCoords(index, sub)

class TriCoords(NamedTuple):
    "An (`index`, `subscript`, `arity`) integer tuple."

    index: int
    "The index integer."

    subscript: int
    "The subscript integer."

    arity: int
    "The arity integer."

    class Sorting(NamedTuple):
        "TriCoords sorting tuple (`subscript`, `index`, `arity`)."

        subscript: int
        "The subscript integer."

        index: int
        "The index integer."

        arity: int
        "The arity integer."

    def sorting(self) -> TriCoords.Sorting:
        "Return the sorting tuple."
        return self.Sorting(self.subscript, self.index, self.arity)

    first = (0, 0, 1)

    def __repr__(self):
        return repr(tuple(self))

BiCoords.first = BiCoords._make(BiCoords.first)
TriCoords.first = TriCoords._make(TriCoords.first)

class TableStore(metaclass = LangCommonMeta):

    default_fetch_key: ClassVar[str]

    _instances: ClassVar[dict[Notation, dict[str, TbsT]]]

    __slots__ = EMPTY_SET

    @classmethod
    def load(cls: type[TbsT], notn: Notation, key: str, data: Mapping, /) -> TbsT:
        # check.inst(key, str)
        notn = Notation[notn]
        idx = cls._instances[notn]
        if key in idx:
            raise Emsg.DuplicateKey((notn, key))
        return idx.setdefault(key, cls(data, (notn, key)))

    @classmethod
    def fetch(cls: type[TbsT], notn: Notation, key: str = None, /) -> TbsT:
        if key is None:
            key = cls.default_fetch_key
        notn = Notation[notn]
        idx = cls._instances[notn]
        try:
            return idx[key]
        except KeyError:
            pass
        store = cls._builtin[notn]
        data = store[key]
        return cls.load(notn, key, data)

    @classmethod
    def available(cls, notn: Notation) -> list[str]:
        notn = Notation(notn)
        idx = cls._instances[notn]
        store = cls._builtin[notn]
        return sorted(set(idx).union(store))

    @classmethod
    def _initcache(cls,
        notns: Iterable[Notation],
        builtin: Mapping[Notation, Mapping[str, Mapping]]
    ):
        if cls is __class__ or hasattr(cls, '_builtin'):
            raise TypeError
        cls._builtin = builtin = MapProxy(dict(builtin))
        notns = set(notns).union(builtin)
        cls._instances = {notn: {} for notn in notns}
        # Prefetch
        for notn in notns:
            # Default for notation.
            cls.fetch(notn)
            # All available.
            for key in cls.available(notn):
                cls.fetch(notn, key)


_RsetSectKT = _enum.Enum|tuple[_enum.Enum, bool]

class RenderSet(TableStore, Mapping[str, Any]):
    'Lexical writer table data class.'

    default_fetch_key = 'ascii'

    notation: Notation
    "The notation."

    renders: Mapping[_RsetSectKT, Callable[..., str]]
    "Render functions."

    strings: Mapping[_RsetSectKT, str]
    "Fixed strings mapping."

    data: Mapping[str, Mapping[_RsetSectKT, Any]]

    keypair: tuple[Notation, str]

    @property
    def charset(self) -> str:
        "The charset name."
        return self['charset']

    @property
    def fetchkey(self) -> str:
        return self.keypair[1]

    __slots__ = (
        '__getitem__',
        'data',
        'keypair',
        'notation',
        'renders',
        'strings',
        'hash',
    )

    def __init__(self, data: Mapping[str, Any], keypair: tuple[Notation, str], /):
        self.data = data = dxopy(data, True)
        self.__getitem__ = data.__getitem__
        self.keypair = keypair
        self.notation = notn = Notation(data['notation'])
        self.renders = data.get('renders', EMPTY_MAP)
        self.strings = data.get('strings', EMPTY_MAP)
        self.hash = self._compute_hash(self)
        notn.charsets.add(self.charset)
        notn.rendersets.add(self)

    def string(self, ctype: Any, value: Any) -> str:
        if ctype in self.renders:
            return self.renders[ctype](value)
        return self.strings[ctype][value]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __reversed__(self):
        return iter(self.data)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if self is other:
            return True
        return type(self) is type(other) and self.data == other.data

    @classmethod
    def _compute_hash(cls, r: RenderSet,) -> int:
        vv = *(*r.renders.values(), *r.strings.values()),
        ktup = *(*r.renders.keys(), *r.strings.keys()),
        vtup = *((*v.items(),) if isinstance(v, Mapping) else v for v in vv),
        return hash((ktup, vtup))


#==================================================+
#  Type aliases -- used a runtime with isinstance  |
#==================================================+

ParameterSpec = BiCoords
"Parameter spec type (BiCoords)."

PredicateSpec = TriCoords
"Predicate spec type (TriCoords)."

AtomicSpec = BiCoords
"Atomic spec type (BiCoords)."

#====================+
#  Generic aliases   |
#====================+

SpecType = tuple[int|str|tuple, ...]
"Tuple with integers, strings, or such nested tuples."

IdentType = tuple[str, SpecType]
"Tuple of (classname, spec)."

ParameterIdent = tuple[str, BiCoords]
"Tuple of (classname, (index, subscript))."

QuantifierSpec = tuple[str]
"Singleton tuple of quantifier name."

OperatorSpec = tuple[str]
"Singleton tuple of operator name."

PredicateRef = tuple[int, ...] | str
"Predicate ref type, int tuple or string."

PredicatedSpec = tuple[TriCoords, tuple[ParameterIdent, ...]]
"Predicated sentence spec type."

QuantifiedSpec = tuple[str, BiCoords, IdentType]
"Quantified sentence spec type."

OperandsSpec = tuple[IdentType, ...]
"Operands argument type."

OperatedSpec = tuple[str, OperandsSpec]
"Operated sentence spec type."

if TYPE_CHECKING:

    # deferred
    PredsItemSpec = PredicateSpec | Predicate
    PredsItemRef  = PredicateRef  | Predicate
    OperCallArg = Iterable[Sentence] | Sentence | OperandsSpec
    QuantifiedItem = Quantifier | Variable | Sentence
    ParseTableKey   = LexType|Marking|type[Predicate.System]
    ParseTableValue = int|Lexical
else:

    PredicateRef = tuple|str

    PredsItemSpec = PredsItemRef = OperCallArg = QuantifiedItem = \
        ParseTableKey = ParseTableValue = object


from pytableaux.lang.lex import (Atomic, Constant, LexType, Operated, Operator,
                                 Predicate, Predicated, Quantified, Quantifier,
                                 Variable)
from pytableaux.lang.parsing import Parser, ParseTable
from pytableaux.lang.writing import LexWriter
