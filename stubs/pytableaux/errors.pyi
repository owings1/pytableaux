from pytableaux.tools import abcs
from typing import Any, Callable, Generic, overload, TypeVar

_E = TypeVar('_E')
_ExT = TypeVar('_ExT', bound = Exception)

class RepeatValueWarning(UserWarning): ...
class IllegalStateError(Exception): ...

class RequestDataError(Exception):
    errors: dict[str, Any]
    def __init__(self, errors: dict[str, Any]) -> None: ...

class TimeoutError(Exception): ...
class ParseError(Exception): ...
class UnboundVariableError(ParseError): ...
class BoundVariableError(ParseError): ...
class MissingAttributeError(AttributeError): ...
class AttributeConflictError(AttributeError): ...
class DuplicateKeyError(KeyError): ...
class MissingKeyError(KeyError): ...
class DuplicateValueError(ValueError): ...
class MissingValueError(ValueError): ...
class ConfigError(ValueError): ...
class ModelValueError(ValueError): ...
class DenotationError(ModelValueError): ...

class Emsg(abcs.Ebc, Generic[_ExT], Callable[..., _ExT]):
    InstCheck: Emsg[TypeError]
    SubclsCheck: Emsg[TypeError]
    NotSubclsCheck: Emsg[TypeError]
    CantJsonify: Emsg[TypeError]
    ReadOnly: Emsg[AttributeError]
    IndexOutOfRange: Emsg[IndexError]
    WrongValue: Emsg[ValueError]
    WrongLength: Emsg[ValueError]
    MismatchSliceSize: Emsg[ValueError]
    MismatchExtSliceSize: Emsg[ValueError]
    ValueConflict: Emsg[ValueError]
    ValueConflictFor: Emsg[ValueError]
    BadAttrName: Emsg[ValueError]
    NotLogicsPackage: Emsg[ValueError]
    BadLogicModule: Emsg[ValueError]
    MissingAttribute: Emsg[MissingAttributeError]
    AttributeConflict: Emsg[AttributeConflictError]
    MissingKey: Emsg[MissingKeyError]
    DuplicateKey: Emsg[DuplicateKeyError]
    DuplicateValue: Emsg[DuplicateValueError]
    MissingValue: Emsg[MissingValueError]
    IllegalState: Emsg[IllegalStateError]
    ThreadRuning: Emsg[IllegalStateError]
    ThreadStopped: Emsg[IllegalStateError]
    Timeout: Emsg[TimeoutError]
    UnknownForSentence: Emsg[ModelValueError]
    ConflictForSentence: Emsg[ModelValueError]
    ConflictForExtension: Emsg[ModelValueError]
    ConflictForAntiExtension: Emsg[ModelValueError]

    msg: str|None
    cls: type[_ExT]
    fns: tuple[Callable[..., str], ...]

    def razr(self, *args) -> None: ...
    def __call__(self:Emsg[_ExT], *args) -> _ExT: ...
    # def __init__(self, * ) -> None: ...

class check:
    @staticmethod
    def inst(obj: Any, classinfo: type[_E]) -> _E: ...
    @staticmethod
    def subcls(obj: Any, typeinfo: _E) -> _E: ...
    @staticmethod
    def callable(obj: _E) -> _E: ...

from warnings import warn as warn

