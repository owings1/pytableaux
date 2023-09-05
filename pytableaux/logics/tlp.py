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
from . import tfde as TFDE


class Meta(KLP.Meta):
    name = 'TLP'
    title = 'LP with T modal'
    description = 'Modal version of LP based on T normal modal logic'
    category_order = 13
    extension_of = ('KLP', 'TFDE')

class Model(TFDE.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = LP.Rules.closure
    groups = TFDE.Rules.groups

