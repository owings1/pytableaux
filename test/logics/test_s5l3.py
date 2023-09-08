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
#
# ------------------
#
# pytableaux.logics.s5l3 tests
from __future__ import annotations

from . import test_l3 as L3Suite

from ..utils import BaseCase

class Base(BaseCase):
    logic = 'S5L3'

class TestRules(Base, autorules=True, bare=True): pass

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, L3Suite.TestTables): pass