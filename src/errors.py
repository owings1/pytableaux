class BadArgumentError(Exception):
    pass

# lexicals

class PredicateError(Exception):
    pass

class IndexTooLargeError(PredicateError):
    pass

class PredicateArityError(PredicateError):
    pass

class PredicateSubscriptError(PredicateError):
    pass

class PredicateAlreadyDeclaredError(PredicateError):
    pass

class NoSuchPredicateError(PredicateError):
    pass

class PredicateArityMismatchError(PredicateError):
    pass

class PredicateIndexMismatchError(PredicateError):
    pass

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

class IllegalStateError(ParseError):
    pass

class UnboundVariableError(ParseError):
    pass

class BoundVariableError(ParseError):
    pass

class UnknownNotationError(ParseError):
    pass