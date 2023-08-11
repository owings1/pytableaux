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
pytableaux.tools.inflect
------------------------
"""
from __future__ import annotations

import re

pat_dashcase1 = re.compile(r'([A-Z]+)')
pat_dashcase2 = re.compile(r'_+')

def dashcase(s: str):
    s = pat_dashcase1.sub(r'-\1', s)
    s = pat_dashcase2.sub(r'-', s)
    return s.lower().strip('-')