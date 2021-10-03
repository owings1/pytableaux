class IllegalStateError(Exception):
    pass

class NotFoundError(ValueError):
    pass
# lexicals

class OperatorError(Exception):
    pass

class NoSuchOperatorError(OperatorError):
    pass

class OperatorArityMismatchError(OperatorError):
    pass

# tableaux

class TableauStateError(Exception):
    pass

class ProofTimeoutError(Exception):
    pass

class TrunkAlreadyBuiltError(TableauStateError):
    pass

class TrunkNotBuiltError(TableauStateError):
    pass

class BranchClosedError(TableauStateError):
    pass

# models
class ModelValueError(Exception):
    pass

class DenotationError(ModelValueError):
    pass

# parsers
class ParseError(Exception):
    pass

class ParserThreadError(ParseError):
    pass

class UnboundVariableError(ParseError):
    pass

class BoundVariableError(ParseError):
    pass

class UnknownNotationError(ParseError):
    pass

# smtp mailroom

class EmailConfigError(Exception):
    pass

class InternalSMTPError(Exception):
    pass
