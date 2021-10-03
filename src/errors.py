# Base Errors
class IllegalStateError(Exception):
    pass

class ParseError(Exception):
    pass

class TimeoutError(Exception):
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

# ParseErrors

class UnboundVariableError(ParseError):
    pass

class BoundVariableError(ParseError):
    pass

class UnknownNotationError(ParseError):
    pass
