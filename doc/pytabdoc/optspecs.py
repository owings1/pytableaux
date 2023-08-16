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
pytabdoc.optspecs
^^^^^^^^^^^^^^^^^

Option specs for roles/directives.
"""
from __future__ import annotations

import re
import docutils.nodes
from pytableaux.lang import Operator, Predicates
from docutils.parsers.rst.directives import class_option as classes
from docutils.parsers.rst.directives import flag as flag


__all__ = (
    'bool_false',
    'bool_true',
    'choice',
    'classes',
    'flag',
    'idnames',
    'nodetype',
    'opers',
    'preds',
    'string',
)

NOARG = object()
re_space = re.compile(r'\s')
re_comma = re.compile(r',')
re_colon = re.compile(r':')
re_nonid = re.compile(r'[^a-zA-Z0-9_]+')

def bool_false(arg: str|None, /) -> bool:
    'Boolean string option, default false.'
    if arg:
        arg = arg.strip()
    else:
        arg = 'on'
    arg = arg.lower()
    if arg in ('true', 'yes', 'on'):
        return True
    if arg in ('false', 'no', 'off'):
        return False
    raise ValueError(f"Invalid boolean value: '{arg}'")

def bool_true(arg: str|None, /) -> bool:
    'Boolean string option, default true.'
    return bool_false(arg or 'true')

def string(arg: str|None, /) -> str:
    'String option, default empty.'
    if arg is None:
        arg = ''
    return arg

def strings(arg: str=NOARG, /, *, splitter=re_comma.split) -> list[str]:
    "Simple splitter, default comma. Spec or spec generator."
    if arg is NOARG:
        return splitter
    return splitter(arg)

def preds(arg: str) -> Predicates:
    """Option spec for list of predicate specs.
    
    NB: not tested or used yet!

    Example::
    
        0:0:1 , 1:0:2
    """
    return Predicates(
        map(int, re_colon.split(spec))
        # remove all whitespace, split on comma
        for spec in re_comma.split(re_space.sub('', arg)))

def opers(arg: str, /) -> list[Operator]:
    """Operators list, from comma-separated input."""
    return list(map(Operator, map(str.strip, re_comma.split(arg))))

def nodetype(arg: str, /) -> type[docutils.nodes.Node]:
    """A docutils node type from a name, e.g. 'inline'."""
    # See roles.setup()
    try:
        return getattr(nodez, arg)
    except AttributeError:
        return getattr(docutils.nodes, arg)

def idnames(arg: str) -> list[str]:
    'Split on one or more non identifier chars.'
    return re_nonid.split(arg)

def choice(choices, /, *, default=NOARG):
    'Option spec builder for choices.'
    def spec(arg: str, /):
        if not arg and default is not NOARG:
            return default
        if arg not in choices:
            raise ValueError(arg)
        return arg
    return spec

from . import nodez
