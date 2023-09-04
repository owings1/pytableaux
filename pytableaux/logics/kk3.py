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
from . import k3 as K3
from . import kfde as KFDE


class Meta(KFDE.Meta):
    name = 'KK3'
    title = 'K3 with K modal'
    description = 'Modal version of K3 based on K normal modal logic'
    values = K3.Meta.values
    designated_values = K3.Meta.designated_values
    unassigned_value = K3.Meta.unassigned_value
    category_order = 20
    extension_of = ('KFDE', 'K3')

class Model(KFDE.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = K3.Rules.closure
    groups = KFDE.Rules.groups

