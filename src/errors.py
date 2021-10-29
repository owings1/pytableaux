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

class UnknownNotationError(ParseError):
    pass

# ValueErrors
class NotFoundError(ValueError):
    pass

class ConfigError(ValueError):
    pass

class ModelValueError(ValueError):
    pass

class DenotationError(ModelValueError):
    pass