# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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

# No local imports!

# __all__ defined at the bottom.

import enum as _enum
from typing import Any

# Base Errors

class IllegalStateError(Exception):
    pass

class RequestDataError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors

class TimeoutError(Exception):
    pass

# ParseErrors

class ParseError(Exception):
    pass

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

def _thru(o): return o
def _len(o): return o if isinstance(o, int) else len(o)

class Emsg(_enum.Enum):

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

    NotLogicsPackage = ValueError, "{0} not a registered logics package", 1
    BadLogicModule = ValueError, "{0} not a value logic module", 1

    MissingAttribute = MissingAttributeError,
    AttributeConflict = AttributeConflictError,

    MissingKey = MissingKeyError,
    DuplicateKey = DuplicateKeyError,

    DuplicateValue = DuplicateValueError,
    MissingValue = MissingValueError,

    IllegalState = IllegalStateError,

    Timeout = TimeoutError, "Timeout of {}ms exceeded", (int,)


class check:

    @staticmethod
    def inst(obj, classinfo: type[_T]) -> _T:
        if not isinstance(obj, classinfo):
            raise Emsg.InstCheck(obj, classinfo)
        return obj

    @staticmethod
    def subcls(cls: type, typeinfo: _T) -> _T:
        if not issubclass(cls, typeinfo):
            raise Emsg.SubclsCheck(cls, typeinfo)
        return cls

instcheck = check.inst
subclscheck = check.subcls

# Some external assembly required.

class EmsgBase:
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

__all__ = 'check', 'Emsg', 'instcheck', 'subclscheck', *(
    name for name, value in locals().items()
    if isinstance(value, type) and issubclass(value, Exception)
)


from typing import TypeVar
_ExT = TypeVar('_ExT', bound = Exception)
_T = TypeVar('_T')

# del(_len, _thru, TypeVar)
