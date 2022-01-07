import typing
_T = typing.TypeVar('_T')

# Base Errors
class IllegalStateError(Exception):
    pass

class TimeoutError(Exception):
    pass

class ActualExpected(Exception):
    'Mixin'
    def __init__(self, act, exp, /, *args):
        self.args = self.fmsg(self.fact(act), self.fexp(exp)), *args

    fmsg = "Got '{0}' but expected '{1}'".format
    fact = fexp = staticmethod(lambda arg: arg)

# Attribute Errors
class ReadOnlyAttributeError(AttributeError):
    def __init__(self, name: str, obj, /, *args, **kw):
        owner = type(obj).__name__
        msg = "'%s' object attribute '%s' is read-only" % (owner, name)
        kw |= dict(name = name, obj = obj)
        super().__init__(msg, *args, **kw)

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

class ValueMismatchError(ValueError, ActualExpected):
    fmsg = "'{0}' does not match '{1}'".format

class ValueLengthError(ValueError, ActualExpected):
    fmsg = "expected value of length {1} but got length {0}".format
    fact = len

class ValueCollisionError(ValueError, ActualExpected):
    fmsg = "'{0}' collides with '{1}'".format

class ConfigError(ValueError):
    pass

class ModelValueError(ValueError):
    pass

class DenotationError(ModelValueError):
    pass

# TypeErrors


class TypeInstCheckError(TypeError, ActualExpected):
    fmsg = "expected type '{1}' but got type '{0}'"
    fact = type

class TypeClassError(TypeError, ActualExpected):
    fmsg = "expected type '{1}' but got type '{0}'"

def instcheck(obj, classinfo: type[_T]) -> _T:
    if not isinstance(obj, classinfo):
        raise TypeInstCheckError(obj, classinfo)
    return obj

def subclscheck(cls: type, typeinfo: _T) -> _T:
    if not issubclass(cls, typeinfo):
        raise TypeClassError(cls, typeinfo)
    return cls

def notsubclscheck(cls: type, typeinfo):
    if issubclass(cls, typeinfo):
        raise TypeError(cls, typeinfo)
    return cls
# Runtime Errors

class SanityError(RuntimeError):
    pass