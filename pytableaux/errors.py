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
pytableaux.errors
^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Callable, TypeVar

if  TYPE_CHECKING:
    from .lang import BiCoords
    from typing import overload

_ExT = TypeVar('_ExT', bound = Exception)
_T = TypeVar('_T')

# No local imports!

# __all__ defined at the bottom.

# warnings

class RepeatValueWarning(UserWarning):
    pass

# Base Errors

class IllegalStateError(Exception):
    pass

class ProofTimeoutError(Exception):
    pass

class TreePruningException(Exception):
    pass

# ParseErrors

class ParseError(Exception):
    pass

class UndefinedPredicateError(ParseError):
    def __init__(self, coords: BiCoords, *args):
        self.coords = coords
        super().__init__(*args)

class UnboundVariableError(ParseError):
    pass

class BoundVariableError(ParseError):
    pass

# AttributeErrors

class MissingAttributeError(AttributeError):
    pass

class AttributeConflictError(AttributeError):
    pass

# KeyErrors

class DuplicateKeyError(KeyError):
    pass

class MissingKeyError(KeyError):
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

# Tree pruning

class SkipDeparture(TreePruningException):
    pass

class SkipNode(TreePruningException):
    pass

def _thru(o): return o
def _len(o): return o if isinstance(o, int) else len(o)

class Emsg(Enum):

    InstCheck = (TypeError,
        "Expected instance of '{1}' but got type '{0}'", (type, _thru))
    SubclsCheck = (TypeError,
        "Expected subclass of '{1}' but got type '{0}'", 2)
    NotSubclsCheck = (TypeError,
        "Unexpected type '{0}', subclass of '{1}'", 2)
    CantJsonify = (TypeError,
        "Object of type {0} is not JSON serializable", (type,))
    Type = TypeError,
    Attribute = AttributeError,

    ReadOnly = (AttributeError,
        "'{0.__name__}' object attribute '{1}' is read-only", (type, str))
    
    IndexOutOfRange = IndexError, 'Index out of range'

    WrongValue = (ValueError,
        "Value '{0}' does not match expected: '{1}'", 2)
    WrongLength = (ValueError,
        "Expected value of length {1} but got length {0}", (_len, _len))
    ArityMismatch = (ValueError,
        "{0} has arity {1} but received input of size {2}", (_thru, _len, _len))
    ValueConflict = ValueError, "Value conflict: '{0}' conflicts with '{1}'", 2
    ValueConflictFor = (ValueError,
        "Value conflict for '{0}': '{1}' conflicts with existing '{2}'", 3)
    BadAttrName = AttributeError, "Invalid attribute identifier: '{}'", (str,)

    NotLogicsPackage = ValueError, "{0} not a registered logics package", 1
    BadLogicModule = ValueError, "{0} not a value logic module", 1

    MissingAttribute = MissingAttributeError, '{}', 1
    AttributeConflict = (AttributeConflictError,
        "Attribute conflict for '{0}': '{1}' conflicts with existing '{2}'", 3)

    MissingKey = MissingKeyError,
    DuplicateKey = DuplicateKeyError,

    DuplicateValue = DuplicateValueError,
    MissingValue = MissingValueError,

    IllegalState = IllegalStateError,
    ThreadRuning = IllegalStateError, "Background thread already running"
    ThreadStopped = IllegalStateError, "Background thread not running"

    Timeout = ProofTimeoutError, "Timeout of {}ms exceeded", (int,)

    UnknownForSentence = (ModelValueError,
        'Non-existent value {0} for sentence {1}', (str, str))
    ConflictForSentence = (ModelValueError,
        'Inconsistent value {0} for sentence {1}', (str, str))
    ConflictForExtension = (ModelValueError,
        'Cannot set value {0} for tuple {1} already in extension', (str, str))
    ConflictForAntiExtension = (ModelValueError,
        'Cannot set value {0} for tuple {1} already in anti-extension', (str, str))

    ParseError = ParseError,

    if TYPE_CHECKING:
        @overload
        def razr(*args): ...

        cls: type[Exception]

class check:

    @staticmethod
    def inst(obj, classinfo: type[_T], err=None) -> _T:
        if not isinstance(obj, classinfo):
            raise Emsg.InstCheck(obj, classinfo) from err
        return obj

    @staticmethod
    def subcls(cls: type, typeinfo: _T) -> _T:
        try:
            issub = issubclass(cls, typeinfo)
        except TypeError:
            issub = False
        if not issub:
            raise Emsg.SubclsCheck(cls, typeinfo)
        return cls

    @staticmethod
    def callable(obj: _T) -> _T:
        if not callable(obj):
            raise Emsg.InstCheck(obj, Callable)
        return obj


from warnings import warn as warn


# Some external assembly required.
class EmsgBase:
    __slots__ = ()
    def __init__(self, cls: type[_ExT], msg: str = None, fns = None):
        if isinstance(cls, tuple):
            cls = type(cls[0], cls[1:], {})
        self.cls = cls
        self.msg = msg
        if fns is None:
            fns = ()
        elif isinstance(fns, int):
            fns = (_thru,) * fns
        self.fns = fns
        def razr(*args):
            raise self._makeas(self.cls, args)
        self.razr = razr
    def __call__(self, *args):
        return self._makeas(self.cls, args)
    def _makeas(self, cls: type[_ExT], args: tuple) -> _ExT:
        return cls(*self._getargs(args))
    def _getargs(self, args: tuple):
        alen = len(self.fns)
        if alen == 0 or len(args) < alen:
            return args
        return self.msg.format(
            *(f(a) for f,a in zip(self.fns, args))
        ), *args[alen:]

__all__ = 'check', 'Emsg', *(
    name for name, value in locals().items()
    if isinstance(value, type) and issubclass(value, (Exception, Warning)))

