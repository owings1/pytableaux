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
# pytableaux - tools.doc.rstutils module
from __future__ import annotations

__all__ = (
    'csvlines',
    'indented',
    'rawblock',
)

import csv
from typing import Iterable

def rawblock(lines: list[str], indent: str|int = None) -> list[str]:
    'Make a raw html block from the lines. Returns a new list of lines.'
    lines = ['.. raw:: html', '', *indented(lines, 4), '']
    return indented(lines, indent)

def indented(lines: Iterable[str], indent: str|int = None) -> list[str]:
    'Indent non-empty lines. Indent can be string or number of spaces.'
    if indent is None:
        indent = ''
    elif isinstance(indent, int):
        indent *= ' '
    return [
        indent + line if len(line) else line
        for line in lines
    ]

def csvlines(rows: list[list[str]], /, indent: str|int = None, quoting = csv.QUOTE_ALL, **kw) -> list[str]:
    'Format rows as CSV lines.'
    lines = []
    w = csv.writer(_csvshim(lines.append), quoting = quoting, **kw)
    w.writerows(rows)
    return indented(lines, indent)

class _csvshim:
    'Many any function into  a ``write()`` method.'
    __slots__ = 'write',
    def __init__(self, func):
        self.write = func