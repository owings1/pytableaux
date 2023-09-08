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
# pytableaux.logics.s5b3e tests
from __future__ import annotations

from unittest import skip

from ..utils import BaseCase
from . import test_b3e as B3ESuite


class Base(BaseCase):
    logic = 'S5B3E'

class TestRules(Base, autorules=True, bare=True): pass

class TestArguments(Base, autoargs=True):
    autoargs_kws = {
        'nested_diamond_within_box1': dict(skip_countermodel=True),
    }

    @skip('TODO: fix model')
    def test_nested_diamond_within_box1_countermodel(self): ...

class TestTables(Base, B3ESuite.TestTables): pass
