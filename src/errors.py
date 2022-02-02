# No local package dependencies.

import enum
import typing
_T = typing.TypeVar('_T')

# Base Errors
class IllegalStateError(Exception):
    pass

class TimeoutError(Exception):
    pass

# ParseErrors

class ParseError(Exception):
    pass

class UnboundVariableError(ParseError):
    pass

class BoundVariableError(ParseError):
    pass

# KeyErrors
class DuplicateKeyError(KeyError):
    pass

# ValueErrors
class DuplicateValueError(ValueError):
    pass

class MissingValueError(ValueError):
    pass

class ConfigError(ValueError):
    pass

class ModelValueError(ValueError):
    pass

class DenotationError(ModelValueError):
    pass

def _thru(o): return o
def _len(o): return o if isinstance(o, int) else len(o)

class Emsg(enum.Enum):
    InstCheck = (TypeError,
        "Expected instance of '{1}' but got type '{0}'", (type, _thru)
    )
    SubclsCheck = (TypeError,
        "Expected subclass of '{1}' but got type '{0}'", 2
    )
    NotSubclsCheck = (TypeError,
        "Unexpected type '{0}', subclass of '{1}'", 2
    )

    ReadOnlyAttr = (AttributeError,
        "'{1.__name__}' object attribute '{0}' is read-only", (str, type)
    )
    # "Read-only attribute: '{0}'", 1
    
    
    IndexOutOfRange = IndexError, 'Index out of range'

    WrongValue = (ValueError,
        "Value '{0}' does not match expected: '{1}'", 2
    )
    WrongLength = (ValueError,
        "Expected value of length '{1}' but got length '{0}'", (_len, _len)
    )
    MismatchSliceSize = (ValueError,
        'Attempt to assign sequence of size {0} to slice of size {1}', (_len, _len)
    )
    MismatchExtSliceSize = (ValueError,
        'Attempt to assign sequence of size {0} to extended slice of size {1}', (_len, _len)
    )
    ValueConflict = ValueError, "Value conflict: '{0}' conflicts with '{1}'", 2
    ValueConflictFor = (ValueError,
        "Value conflict for '{0}': '{1}' conflicts with existing '{2}'", 3
    )
    BadAttrName = ValueError, "Invalid attribute identifier: '{}'", (str,)

    DuplicateValue = DuplicateValueError,
    MissingValue = MissingValueError,

    DuplicateKey = DuplicateKeyError,

    def __init__(self, cls, msg: str = None, fns = None):
        if isinstance(cls, tuple):
            cls = type(cls[0], cls[1:], {})
        self.cls = cls
        self.msg = msg
        if fns is None: fns = ()
        elif isinstance(fns, int): fns = (_thru,) * fns
        self.fns = fns
    def __call__(self, *args):
        return self._makeas(self.cls, args)
    def throw(self, *args):
        raise self._makeas(self.cls, args)
    def throwas(self, cls, *args):
        raise self._makeas(cls, args)
    def _makeas(self, cls, args):
        return cls(*self._getargs(args))
    def _getargs(self, args):
        alen = len(self.fns)
        if alen == 0 or len(args) < alen: return args
        return self.msg.format(
            *(f(a) for f,a in zip(self.fns, args))
        ), *args[alen:]

def instcheck(obj, classinfo: type[_T]) -> _T:
    if not isinstance(obj, classinfo):
        raise Emsg.InstCheck(obj, classinfo)
    return obj

def subclscheck(cls: type, typeinfo: _T) -> _T:
    if not issubclass(cls, typeinfo):
        raise Emsg.SubclsCheck(cls, typeinfo)
    return cls

def notsubclscheck(cls: type, typeinfo):
    if issubclass(cls, typeinfo):
        raise Emsg.NotSubclsCheck(cls, typeinfo)
    return cls

def errstr(err) -> str:
    if isinstance(err, Exception):
        return '%s: %s' % (type(err).__name__, err)
    return str(err)

del(enum)