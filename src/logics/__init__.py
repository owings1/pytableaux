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
#
# ------------------
#
# pytableaux - logics package
from __future__ import annotations
from importlib import import_module
from types import ModuleType
from tools import closure
_lookup = {}

def getlogic(ref) -> ModuleType:
    """Get the logic module from the specified reference.

    Each of following examples returns the L{FDE} logic module::

        getlogic('fde')
        getlogic('FDE')
        getlogic('logics.fde')
        getlogic(getlogic('FDE'))

    :param any ref: The logic reference.
    :return: The logic module.
    :rtype: module
    :raises ValueError: if the module is not a logic.
    :raises ModuleNotFoundError: if the module is not found.
    :raises TypeError: if no module name can be determined from ``ref``.
    """
    idx = _lookup
    try:
        return idx[ref]
    except KeyError:
        pass
    try:
        return idx[ref.__module__.lower()]
    except AttributeError:
        pass
    except KeyError:
        ref = import_module(ref.__module__)
    if isinstance(ref, ModuleType):
        if ref.__package__ != __package__ or ref.__name__ == __name__:
            raise ValueError(f'{ref} is not a logic module')
        key = ref.__name__.lower()
        try:
            logic = idx[key]
        except KeyError:
            pass
        else:
            if logic is not ref:
                raise ValueError(f'{ref} does not match stored {logic}')
        idx[ref.name] = idx[ref.name.lower()] = ref
        idx[key] = idx[ref] = ref
        return ref
    if not isinstance(ref, str):
        raise TypeError("ref must be string or module, or have __module__ attribute")
    key = ref.lower()
    try:
        logic = idx[key]
    except KeyError:
        pass
    else:
        return logic
    if key == __name__:
        raise ValueError(f'{ref} is not a logic module')
    if '.' not in key:
        key = f'{__name__}.{key}'
    elif not key.startswith(__name__ + '.'):
        raise ValueError(f'{key} is not in package {__package__}')
    cand = import_module(key)
    if cand.__package__ != __package__:
        raise ValueError(f'{cand} is not in package {__package__}')
    idx[cand.name] = idx[cand.name.lower()] = cand
    idx[key] = idx[cand] = cand
    return cand

