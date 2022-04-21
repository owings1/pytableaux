from __future__ import annotations

__all__ = (
    'BiCoords',
    'TriCoords',

    'LangCommonMeta',
    'LangCommonEnumMeta',
    'ArgumentMeta',

    'ParserMeta',

    'LangCommonEnum',

    'Notation',
    'Marking',

    'TableStore',
    'RenderSet',

    'nosetattr',
    'raiseae',

    # aliases
    'PredicateSpec',
    'ParameterSpec',
    'AtomicSpec',

    # Generic alias
    'SpecType', 'IdentType',  'ParameterIdent', 'QuantifierSpec',
    'OperatorSpec',  'PredicateRef',  'PredicatedSpec',
    'QuantifiedSpec', 'OperandsSpec', 'OperatedSpec',
    # Generic alias (deferred)
    'PredsItemSpec', 'PredsItemRef', 'OperCallArg', 'QuantifiedItem',
    'ParseTableKey', 'ParseTableValue',

    # Type variables
    'TbsT', 'CrdT', 'LexT', 'LexItT', 'SenT',
)

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable, Mapping, NamedTuple, TypeVar

from pytableaux.errors import Emsg, check
from pytableaux.tools import abcs, closure, MapProxy
from pytableaux.tools.decorators import NoSetAttr, raisr
from pytableaux.tools.sets import setm, EMPTY_SET

if TYPE_CHECKING:
    from pytableaux.lang.parsing import Parser
    from pytableaux.lexicals import Quantifier, Variable
    from pytableaux.lexicals import (CoordsItem, Lexical, LexicalItem,
                                     LexWriter, Sentence,
                                     Predicate, LexType)

nosetattr = NoSetAttr(attr = '_readonly', enabled = False)
raiseae = raisr(AttributeError)

#==========================+
#  Meta classes            |
#==========================+

class LangCommonMeta(abcs.AbcMeta):
    """Common metaclass for lang classes. The nosetattr member is
    shared among these classes and is activated after the modules are fully
    initialized.
    """
    _readonly : bool
    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.AbcMeta)

class LangCommonEnumMeta(abcs.EnumMeta):
    'Common Enum metaclass for lang classes.'
    _readonly : bool
    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.EnumMeta)

class ArgumentMeta(LangCommonMeta):
    'Argument Metaclass.'

    def __call__(cls, *args, **kw):
        if len(args) == 1 and not len(kw) and isinstance(args[0], cls):
            return args[0]
        return super().__call__(*args, **kw)

class ParserMeta(LangCommonMeta):
    'Parser Metaclass.'

    def __call__(cls, *args, **kw):
        if cls is Parser:
            if args:
                notn = Notation(args[0])
                args = args[1:]
            else:
                notn = Notation.default
            return notn.Parser(*args, **kw)
        return super().__call__(*args, **kw)

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

    polish   = abcs.eauto(), 'unicode'
    standard = abcs.eauto(), 'unicode'

    def __init__(self, num, default_charset: str, /):
        self.charsets = setm((default_charset,))
        self.default_charset = default_charset
        self.writers = setm()
        self.DefaultWriter = None
        self.rendersets = setm()

    __slots__ = (
        'Parser',
        'writers', 'DefaultWriter',
        'rendersets', 'charsets', 'default_charset',
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
        def __setattr__(self, name, value):
            if name == 'Parser' and not hasattr(self, name):
                Enum.__setattr__(self, name, value)
            else:
                super().__setattr__(name, value)
        return __setattr__

class Marking(LangCommonEnum):
    'Miscellaneous marking/punctuation enum.'

    paren_open  = abcs.eauto()
    paren_close = abcs.eauto()
    whitespace  = abcs.eauto()
    digit       = abcs.eauto()
    meta        = abcs.eauto()
    subscript   = abcs.eauto()

#==========================+
#  Aux classes             |
#==========================+

class BiCoords(NamedTuple):
    index     : int
    subscript : int

    class Sorting(NamedTuple):
        subscript : int
        index     : int

    def sorting(self) -> BiCoords.Sorting:
        return self.Sorting(self.subscript, self.index)

    first = (0, 0)

    def __repr__(self):
        return repr(tuple(self))

class TriCoords(NamedTuple):
    index     : int
    subscript : int
    arity     : int

    class Sorting(NamedTuple):
        subscript : int
        index     : int
        arity     : int

    def sorting(self) -> TriCoords.Sorting:
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
        check.inst(key, str)
        notn = Notation[notn]
        idx = cls._instances[notn]
        if key in idx:
            raise Emsg.DuplicateKey((notn, key))
        return idx.setdefault(key, cls(data))

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

class RenderSet(TableStore):
    'Lexical writer table data class.'

    default_fetch_key = 'ascii'

    notation: Notation
    charset: str
    renders: Mapping[Any, Callable[..., str]]
    strings: Mapping[Any, str]
    data: Mapping[str, Any]

    def __init__(self, data: Mapping[str, Any]):
        self.notation = notn = Notation(data['notation'])
        self.charset = data['charset']
        self.renders = data.get('renders', {})
        self.strings = data.get('strings', {})
        self.data = data
        notn.charsets.add(self.charset)
        notn.rendersets.add(self)

    def string(self, ctype: Any, value: Any) -> str:
        if ctype in self.renders:
            return self.renders[ctype](value)
        return self.strings[ctype][value]

#==================================================+
#  Type aliases -- used a runtime with isinstance  |
#==================================================+

ParameterSpec  = BiCoords

PredicateSpec = TriCoords

AtomicSpec     = BiCoords

#==============================================+
#  Generic aliases -- no 'isinstance' support  |
#==============================================+

SpecType = tuple[int|str|tuple, ...]
"Tuple with integers, strings, or such nested tuples."

IdentType = tuple[str, SpecType]
"Tuple of (classname, spec)"

ParameterIdent = tuple[str, BiCoords]

QuantifierSpec = tuple[str]

OperatorSpec   = tuple[str]

PredicateRef  = tuple[int, ...] | str

PredicatedSpec = tuple[TriCoords, tuple[ParameterIdent, ...]]

QuantifiedSpec = tuple[str, BiCoords, IdentType]

OperandsSpec   = tuple[IdentType, ...]

OperatedSpec   = tuple[str, OperandsSpec]

if TYPE_CHECKING:
    # deferred
    PredsItemSpec = PredicateSpec | Predicate
    PredsItemRef  = PredicateRef  | Predicate
    OperCallArg = Iterable[Sentence] | Sentence | OperandsSpec
    QuantifiedItem = Quantifier | Variable | Sentence
    ParseTableKey   = LexType|Marking|type[Predicate.System]
    ParseTableValue = int|Lexical
else:
    PredsItemSpec = PredsItemRef = OperCallArg = QuantifiedItem = \
        ParseTableKey = ParseTableValue = object

#==========================+
#  Type variables          |
#==========================+

TbsT   = TypeVar('TbsT',   bound = 'TableStore')
"TypeVar bound to `TableStore`."

CrdT   = TypeVar('CrdT',   bound = 'CoordsItem')
"TypeVar bound to `CoordsItem`."

LexT   = TypeVar('LexT',   bound = 'Lexical')
"TypeVar bound to `Lexical`."

LexItT = TypeVar('LexItT', bound = 'LexicalItem')
"TypeVar bound to `LexicalItem`."

SenT   = TypeVar('SenT',   bound = 'Sentence')
"TypeVar bound to `Sentence`."
