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
from typing import Any, Callable, Mapping

__all__ = ()

from pytableaux.tools import closure

from itertools import islice
from types import ModuleType

def dcopy(a: Mapping, /) -> dict:
    'Basic dict copy of a mapping, recursive for mapping values.'
    return {
        key: dcopy(value)
            if isinstance(value, Mapping)
            else value
        for key, value in a.items()
    }

def dmerged(a: dict, b: dict, /) -> dict:
    'Basic dict merge copy, recursive for dict value.'
    c = {}
    for key, value in b.items():
        if isinstance(value, dict):
            avalue = a.get(key)
            if isinstance(avalue, dict):
                c[key] = dmerged(a[key], value)
            else:
                c[key] = dcopy(value)
        else:
            c[key] = value
    for key in a:
        if key not in c:
            c[key] = a[key]
    return c

@closure
def dtransform():

    def _true(_): True

    def api(transformer: Callable[[Any], Any], a: dict, /,
        typeinfo: type|tuple[type, ...] = dict,
        inplace = False,
    ) -> dict:

        if typeinfo is None:
            pred = _true
        else:
            pred = lambda v: isinstance(v, typeinfo)
        res = runner(transformer, pred, inplace, a)
        if not inplace:
            return res

    def runner(f, pred, inplace, a: dict):
        if inplace:
            b = a
        else:
            b = {}
        for k, v in a.items():
            if isinstance(v, dict):
                b[k] = runner(f, pred, inplace, v)
            elif pred(v):
                b[k] = f(v)
            else:
                b[k] = v
        return b

    return api

def cat(*args: str) -> str:
    'Concat all argument strings'
    return ''.join(args)

def wrparens(*args: str, parens='()') -> str:
    'Concat all argument strings and wrap in parentheses'
    return cat(parens[0], ''.join(args), parens[-1])

def drepr(d: dict, /, limit = 10, j: str = ', ', vj = '=', paren = True) -> str:
    lw = drepr.lw
    istr = j.join(
        f'{k}{vj}{valrepr(v, lw = lw)}'
        for k,v in islice(d.items(), limit)
    )
    assert not paren
    # if paren:
    #     return wrparens(istr)
    return istr
# For testing, set this to a LexWriter instance.
drepr.lw = None

def valrepr(v, /, lw = None) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, type):
        return v.__name__
    if isinstance(v, ModuleType) and 'logics.' in v.__name__:
        return getattr(v, 'name', v.__name__)
    if lw is None:
        lw = drepr.lw
    if lw is not None and lw.canwrite(v):
        return lw(v)
    # try:
    #     return lw(v)
    # except TypeError:
    #     pass
    return repr(v)

def orepr(obj, d: dict = None, /, **kw) -> str:
    if d is None:
        d = kw
    elif len(kw):
        d = dict(d, **kw)
    oname = type(obj).__qualname__
    try:
        dstr = drepr(d, j = ' ', vj = ':', paren = False)
        if dstr:
            return f'<{oname} {dstr}>'
        return f'<{oname}>'
    except Exception as e:
        from pytableaux.errors import errstr
        return '<%s !ERR: %s !>' % (oname, errstr(e))

def wraprepr(obj, inner, **kw) -> str:
    if not isinstance(obj, str):
        obj = type(obj).__name__
    return cat(obj, wrparens(inner.__repr__(), **kw))