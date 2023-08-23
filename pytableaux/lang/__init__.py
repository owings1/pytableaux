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
pytableaux.lang
---------------

"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from types import MappingProxyType as MapProxy
from typing import Any, ClassVar, Iterable, NamedTuple, Self

from ..errors import Emsg
from ..tools import EMPTY_MAP, EMPTY_SET, NoSetAttr, abcs, closure, dxopy

__all__ = (
    # Classes
    # 'BiCoords',
    # 'LangCommonEnum',
    # 'LangCommonEnumMeta',
    # 'LangCommonMeta',
    # 'LexicalAbcMeta',
    'Marking',
    'Notation',
    'StringTable',
    # 'TableStore',
    # 'TriCoords',

    # Subpackage export
    'Argument',
    'Atomic',
    'Constant',
    'CoordsItem',
    'Lexical',
    'LexicalAbc',
    'LexicalEnum',
    'LexType',
    'LexWriter',
    'Operated',
    'Operator',
    'Parameter',
    'Parser',
    'ParseTable',
    'Predicate',
    'Predicated',
    'Predicates',
    'Quantified',
    'Quantifier',
    'Sentence',
    'Variable')

nosetattr = NoSetAttr(attr = '_readonly', enabled = False)

#==========================+
#  Meta classes            |
#==========================+

class LangCommonMeta(abcs.AbcMeta):
    "Common metaclass for lang classes."
    
    # The nosetattr member is shared among these classes and is activated after
    # the modules are fully initialized.

    def __prepare__(clsname, bases, **kw):
        return dict(__slots__=EMPTY_SET)

    _readonly : bool
    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = nosetattr(abcs.AbcMeta)

class LangCommonEnumMeta(abcs.EbcMeta):
    'Common Enum metaclass for lang classes.'

    _readonly : bool
    # Set in base __init__ for Python 3.11 Enum compat
    # __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = nosetattr(abcs.EbcMeta)

class LexicalAbcMeta(LangCommonMeta):
    "Common metaclass for non-Enum lexical classes."

    # Populated in lex module.
    __call__ = NotImplemented

#==========================+
#  Base classes            |
#==========================+

class LangCommonEnum(abcs.Ebc, metaclass=LangCommonEnumMeta):
    'Common Enum base class for lang classes.'

    # __slots__   = 'value', '_value_', '_name_',

    # Set in base __init__ for Python 3.11 Enum compat
    # __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = nosetattr(abcs.Ebc, cls = True)

#==========================+
#  Enum classes            |
#==========================+

class Notation(LangCommonEnum):
    'Notation (polish/standard) enum class.'

    default: ClassVar[Notation]
    "The default notation."

    formats: dict[str, set[StringTable]]
    "Mapping from format to set of string tables for the notation."

    default_format: str
    "The render format of the notation's default writer."

    writers: set[type[LexWriter]]
    "All writer classes for the notation."

    DefaultWriter: type[LexWriter]
    "The notations's default writer class."

    Parser: type[Parser]
    "The notation's parser class."

    #--- Members

    polish = 'polish',
    "Polish notation."

    standard = 'standard',
    "Standard notation."

    def __init__(self, name, /):
        default_format = 'ascii'
        self.formats = defaultdict(set)
        self.formats[default_format]
        self.default_format = default_format
        self.writers = set()
        self.DefaultWriter = None

    __slots__ = (
        'formats',
        'default_format',
        'DefaultWriter',
        'Parser',
        'writers')

    @classmethod
    def get_common_formats(cls) -> list[str]:
        "Get formats common to all notations."
        formats: set[str] = set(
            format
            for notn in Notation
                for format in notn.formats)
        for notn in Notation:
            formats.intersection_update(notn.formats)
        return sorted(formats)

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

    @classmethod
    def _member_keys(cls, member: Notation, /):
        return super()._member_keys(member).union({member.name.capitalize()})

    @abcs.abcf.after
    def _(cls):
        cls.default = cls.polish


class Marking(str, LangCommonEnum):
    'Miscellaneous marking/punctuation enum.'

    paren_open = 'paren_open'
    "Open parenthesis marking."

    paren_close = 'paren_close'
    "Close parenthesis marking."

    whitespace = 'whitespace'
    "Whitespace marking."

    digit = 'digit'
    "Digit marking."

    meta = 'meta'
    "Meta marking."

    subscript = 'subscript'
    "Subscript marking."

    tableau = 'tableau'
    "Tableau marking."

    subscript_open = 'subscript_open'
    subscript_close = 'subscript_close'

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

    def sorting(self):
        "Return the sorting tuple."
        return self.Sorting(self.subscript, self.index)

    first = (0, 0)

    def __repr__(self):
        return repr(tuple(self))

    @classmethod
    def make(cls, it: Iterable):
        if isinstance(it, Mapping):
            it = map(it.__getitem__, cls._fields)
        return cls._make(it)

    @staticmethod
    def min_unused(used, maxi):
        # finds the mimimum available by searching for gaps.
        if not used:
            return BiCoords.first
        index = 0
        sub = 0
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

    def sorting(self):
        "Return the sorting tuple."
        return self.Sorting(self.subscript, self.index, self.arity)

    first = (0, 0, 1)

    def __repr__(self):
        return repr(tuple(self))

    @classmethod
    def make(cls, it: Iterable):
        if isinstance(it, Mapping):
            it = map(it.__getitem__, cls._fields)
        return cls._make(it)

BiCoords.first = BiCoords.make(BiCoords.first)
TriCoords.first = TriCoords.make(TriCoords.first)


class TableStore(metaclass=LangCommonMeta):

    default_fetch_key: ClassVar[str]

    _instances: ClassVar[dict[Notation, dict[Any, Self]]]

    __slots__ = EMPTY_SET

    @classmethod
    def load(cls, notn, key, data, /):
        """Create and store instance from data.

        Args:
            notn: The notation
            key: The unique key
            data: The data mapping

        Raises:
            Emsg.DuplicateKey: on duplicate key for notation

        Returns:
            The instance
        """
        notn = Notation[notn]
        idx = cls._instances[notn]
        if key in idx:
            raise Emsg.DuplicateKey((notn, key))
        return idx.setdefault(key, cls(data, (notn, key)))

    @classmethod
    def fetch(cls, notn, key = None, /):
        """Get a loaded instance.

        Args:
            notn: The notation
            key: The unique key. Defaults to class default.

        Returns:
            The instance
        """        
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
    def available(cls, notn):
        """List the loaded keys for a notation.

        Args:
            notn: The notation

        Returns:
            list: The sorted keys
        """        
        notn = Notation(notn)
        idx = cls._instances[notn]
        store = cls._builtin[notn]
        return sorted(set(idx).union(store))

    @classmethod
    def _initcache(cls, notns, builtin):
        if cls is __class__ or hasattr(cls, '_builtin'):
            raise TypeError
        cls._builtin = MapProxy(dict(builtin))
        notns = set(notns).union(cls._builtin)
        cls._instances = {notn: {} for notn in notns}
        # Prefetch
        for notn in notns:
            # Default for notation.
            cls.fetch(notn)
            # All available.
            for key in cls.available(notn):
                cls.fetch(notn, key)


class StringTable(TableStore, Mapping):
    'Lexical writer strings table data class.'

    default_fetch_key = 'ascii'

    strings: Mapping
    "Fixed strings mapping."

    data: Mapping
    keypair: tuple

    @property
    def format(self) -> str:
        "The format (html, latex, etc.)"
        return self.data['format']

    @property
    def notation(self) -> Notation:
        "The notation flavor."
        return self.data['notation']

    @property
    def fetchkey(self) -> str:
        return self.keypair[1]

    __slots__ = (
        'data',
        'keypair',
        'flat',
        'hash')

    def __init__(self, data: Mapping, keypair: tuple, /):
        self.data = dxopy(data, True)
        self.flat = {}
        self.keypair = keypair
        self.hash = self._compute_hash()
        self.notation.formats[self.format].add(self)
        for key, value in self.data['strings'].items():
            if isinstance(key, tuple):
                path = key
            else:
                path = key,
            if isinstance(value, tuple):
                for i, value in enumerate(value):
                    self.flat[*path, i] = value
                continue
            if isinstance(value, Mapping):
                for key, value in value.items():
                    if isinstance(key, tuple):
                        keys = key
                    else:
                        keys = key,
                    self.flat[*path, *keys] = value
                continue
            raise ValueError(value)

    def __getitem__(self, key):
        return self.flat[key]

    def __len__(self):
        return len(self.flat)

    def __iter__(self):
        return iter(self.flat)

    def __reversed__(self):
        return reversed(self.flat)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if self is other:
            return True
        return (
            type(self) is type(other) and
            hash(self) == hash(other) and
            self.format == other.format)

    def _compute_hash(self) -> int:
        return hash(tuple(sorted(self.items())))


from .lex import Atomic, Constant
from .lex import CoordsItem as CoordsItem
from .lex import Lexical as Lexical
from .lex import LexType as LexType
from .lex import Operated as Operated
from .lex import Operator as Operator
from .lex import Parameter as Parameter
from .lex import LexicalAbc as LexicalAbc
from .lex import LexicalEnum as LexicalEnum

pass

from .lex import Predicate as Predicate
from .lex import Predicated as Predicated
from .lex import Quantified as Quantified
from .lex import Quantifier as Quantifier
from .lex import Sentence as Sentence
from .lex import Variable as Variable

pass
from .parsing import Parser as Parser
from .parsing import DefaultParser as DefaultParser
from .parsing import ParseTable as ParseTable
from .parsing import PolishParser as PolishParser
from .parsing import StandardParser as StandardParser

pass
from .collect import Argument as Argument
from .collect import Predicates as Predicates

pass
from .writing import LexWriter as LexWriter
from .writing import DefaultLexWriter as DefaultLexWriter
from .writing import PolishLexWriter as PolishLexWriter
from .writing import StandardLexWriter as StandardLexWriter


@closure
def init():

    from . import _symdata

    StringTable._initcache(Notation, _symdata.string_tables())
    ParseTable._initcache(Notation, _symdata.parsetables())
    LexWriter._sys = LexWriter('standard', 'unicode')

    def tostr_item(item: LexicalAbc):
        return LexWriter._sys(item)

    def tostr_enum(enum: LexicalEnum):
        return enum.name

    def tostr_pred(pred: Predicate):
        try:
            if pred.is_system:
                return pred.name
        except AttributeError:
            pass
        return tostr_item(pred)

    LexicalEnum.__str__ = tostr_enum
    LexicalAbc.__str__ = tostr_item
    Predicate.__str__ = tostr_pred

    def repr_lex(obj: Lexical):
        try:
            return f'<{obj.TYPE.role.__name__}: {obj}>'
        except AttributeError:
            return object.__repr__(obj)

    Lexical.__repr__ = repr_lex

    from . import lex
    from ..errors import Emsg

    for cls in (LangCommonEnumMeta, LangCommonEnum):
        cls.__delattr__ = Emsg.ReadOnly.razr

    for cls in (LangCommonEnum, LexicalAbc, Predicates, Argument, Lexical):
        cls._readonly = True

    lex.nosetattr.enabled = True
    lex.nosetattr.cache.clear()

    del(lex.nosetattr)

del(init)