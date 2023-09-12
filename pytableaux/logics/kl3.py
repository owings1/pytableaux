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

from . import kfde as KFDE
from . import l3 as L3


class Meta(L3.Meta, KFDE.Meta):
    name = 'KL3'
    title = 'L3 with K modal'
    description = 'Modal version of L3 based on K normal modal logic'
    category_order = 16
    extension_of = ('L3')

class Model(L3.Model, KFDE.Model): pass
class System(L3.System, KFDE.System): pass

class Rules(L3.Rules, KFDE.Rules):

    groups = (
        *L3.Rules.nonbranching_groups,
        *L3.Rules.branching_groups,
        *KFDE.Rules.unmodal_groups,
        *L3.Rules.unquantifying_groups)
