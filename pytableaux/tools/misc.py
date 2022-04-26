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
pytableaux.tools.misc
^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from itertools import islice
from typing import Any, Callable, Mapping

from pytableaux.tools import closure

__all__ = ()

class track:
    """Track additions change updates to locals.
    
    Usage::

        a = 1
        b = 2
    
        with track(locals()) as ns:
            b = 3
            c = 4
    
    The value of ``ns`` will be ``{'b': 3, 'c': 4}``
    """
    __slots__ = 'ref', 'builder'
    def __init__(self, ref: Mapping):
        self.ref = ref
    def __enter__(self):
        self.builder = dict(self.ref)
        return self.builder
    def __exit__(self, typ, vlu, traceback):
        builder = self.builder
        diff = {}
        for key, value in self.ref.items():
            if builder.get(key, builder) is not value:
                if value is not builder:
                    diff[key] = value
        builder.clear()
        builder.update(diff)


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

def drepr(d: dict, /, limit = 10, j: str = ', ', vj = '=', paren = True) -> str:
    lw = drepr.lw
    istr = j.join(
        f'{k}{vj}{valrepr(v, lw = lw)}'
        for k,v in islice(d.items(), limit)
    )
    assert not paren
    return istr
# For testing, set this to a LexWriter instance.
drepr.lw = None

def valrepr(v, /, lw = None) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, type):
        return v.__name__
    if lw is None:
        lw = drepr.lw
    if lw is not None and lw.canwrite(v):
        return lw(v)
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
        return f'<{oname} !ERR: {repr(e)} !>'
