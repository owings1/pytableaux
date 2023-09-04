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
from __future__ import annotations

from . import LogicType
from . import fde as FDE
from . import lp as LP
from . import klp as KLP
from . import s4fde as S4FDE


class Meta(KLP.Meta):
    name = 'S4LP'
    title = 'LP with S4 modal'
    description = 'Modal version of LP based on S4 normal modal logic'
    category_order = 1003
    extension_of = ('TLP', 'S4FDE')

class Model(S4FDE.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = LP.Rules.closure
    groups = S4FDE.Rules.groups

