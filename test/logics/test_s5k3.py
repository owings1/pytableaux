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
# pytableaux.logics.s5k3 tests
from __future__ import annotations

from ..utils import BaseCase
from . import test_k3 as K3Suite
from .test_s5 import TestArguments as S5Arguments


class Base(BaseCase):
    logic = 'S5K3'

class TestRules(Base, autorules=True, bare=True): pass

class TestArguments(Base, autoargs=True):
    test_valid_optimize_nec_rule1 = S5Arguments.test_valid_optimize_nec_rule1
    test_valid_intermediate_mix_modal_quantifiers1 = S5Arguments.test_valid_intermediate_mix_modal_quantifiers1

class TestTables(Base, K3Suite.TestTables): pass