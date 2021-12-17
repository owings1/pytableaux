# Base Errors
class IllegalStateError(Exception):
    pass

class TimeoutError(Exception):
    pass

# Attribute Errors
class ReadOnlyAttributeError(AttributeError):
    def __init__(self, name: str, obj, /, *args, **kw):
        owner = type(obj).__name__
        msg = "'%s' object attribute '%s' is read-only" % (owner, name)
        kw |= dict(name = name, obj = obj)
        super().__init__(msg, *args, **kw)
        # super().__init__(msg, *args, name = name, obj = obj, **kw)
# ParseErrors

class ParseError(Exception):
    pass

class UnboundVariableError(ParseError):
    pass

class BoundVariableError(ParseError):
    pass

class UnknownNotationError(ParseError):
    pass

# KeyErrors
class DuplicateKeyError(KeyError):
    pass

# ValueErrors
class DuplicateValueError(ValueError):
    pass

class ValueMismatchError(ValueError):
    def __init__(self, lhs, rhs, /, *args, **kw):
        msg = "'%s' does not match '%s'" % (lhs, rhs)
        super().__init__(msg, *args, **kw)
    pass

class NotFoundError(ValueError):
    pass

class ConfigError(ValueError):
    pass

class ModelValueError(ValueError):
    pass

class DenotationError(ModelValueError):
    pass

# TypeErrors
