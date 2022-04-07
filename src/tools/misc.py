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
# pytableaux - tools.misc module
from __future__ import annotations

__all__ = 'get_logic',

# No local imports

from builtins import ModuleNotFoundError
from importlib import import_module
from itertools import islice
from types import ModuleType

def get_module(ref, package: str = None) -> ModuleType:

    cache = get_module.__dict__
    keys = set()
    ret = {'mod': None}

    def _checkref(ref):
        if ref is None: return
        key = (package, ref)
        try: return bool(_setcache(cache[key]))
        except KeyError: keys.add(key)
        return False

    def _setcache(val):
        for key in keys:
            cache[key] = val
        ret['mod'] = val
        return val

    if hasattr(ref, '__module__'):
        if _checkref(ref.__module__):
            return ret['mod']
        ref = import_module(ref.__module__)

    if isinstance(ref, ModuleType):
        if _checkref(ref.__name__):
            return ret['mod']
        if package is not None and package != getattr(ref, '__package__', None):
            raise ModuleNotFoundError(
                "Module '{0}' not in package '{1}'".format(ref.__name__, package)
            )
        return _setcache(ref)

    if not isinstance(ref, str):
        raise TypeError("ref must be string or module, or have __module__ attribute")

    ref = ref.lower()
    if _checkref(ref):
        return ret['mod']
    if package is None:
        return _setcache(import_module(ref))
    pfx = cat(package, '.')
    try:
        return _setcache(import_module(cat(pfx, ref)))
    except ModuleNotFoundError:
        if not ref.startswith(pfx):
            raise
        ref = ref[len(pfx):]
        if _checkref(ref):
            return ret['mod']
        return _setcache(import_module(cat(pfx, ref)))

def get_logic(ref) -> ModuleType:
    """
    Get the logic module from the specified reference.

    Each of following examples returns the L{FDE} logic module::

        get_logic('fde')
        get_logic('FDE')
        get_logic('logics.fde')
        get_logic(get_logic('FDE'))


    :param any ref: The logic reference.
    :return: The logic module.
    :rtype: module
    :raises ModuleNotFoundError: if the logic is not found.
    :raises TypeError: if no module name can be determined from ``ref``.
    """
    return get_module(ref, package = 'logics')

def cat(*args: str) -> str:
    'Concat all argument strings'
    return ''.join(args)

def wrparens(*args: str, parens='()') -> str:
    'Concat all argument strings and wrap in parentheses'
    return cat(parens[0], ''.join(args), parens[-1])

def drepr(d: dict, limit = 10, j: str = ', ', vj = '=', paren = True) -> str:
    lw = drepr.lw
    pairs = (
        cat(str(k), vj, valrepr(v, lw = lw))
        for k,v in islice(d.items(), limit)
    )
    istr = j.join(pairs)
    if paren:
        return wrparens(istr)
    return istr
# For testing, set this to a LexWriter instance.
drepr.lw = None

def valrepr(v, lw = drepr.lw, **opts) -> str:
    if isinstance(v, str): return v
    if isinstance(v, type): return v.__name__
    if isinstance(v, ModuleType):
        if v.__name__.startswith('logics.'):
            return getattr(v, 'name', v.__name__)
    try: return lw(v)
    except TypeError: pass
    return v.__repr__()

def orepr(obj, _d: dict = None, _ = None, **kw) -> str:
    d = _d if _d is not None else kw
    if isinstance(obj, str):
        oname = obj
    else:
        try: oname = type(obj).__qualname__
        except AttributeError: oname = type(obj).__name__
    if _ is not None: oname = cat(oname, '.', valrepr(_))
    try:
        if callable(d): d = d()
        dstr = drepr(d, j = ' ', vj = ':', paren = False)
        if dstr:
            return '<%s %s>' % (oname, dstr)
        return '<%s>' % oname
    except Exception as e:
        from errors import errstr
        return '<%s !ERR: %s !>' % (oname, errstr(e))

def wraprepr(obj, inner, **kw) -> str:
    if not isinstance(obj, str):
        obj = type(obj).__name__
    return cat(obj, wrparens(inner.__repr__(), **kw))

