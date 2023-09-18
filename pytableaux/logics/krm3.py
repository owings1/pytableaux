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
from . import rm3 as RM3


class Meta(RM3.Meta, KFDE.Meta):
    name = 'KRM3'
    title = 'RM3 with K modal'
    description = 'Modal version of RM3 based on K normal modal logic'
    category_order = KFDE.Meta.category_order + 20
    extension_of = ('RM3')

class Model(RM3.Model, KFDE.Model): pass
class System(RM3.System, KFDE.System): pass

class Rules(RM3.Rules, KFDE.Rules):

    groups = (
        *RM3.Rules.nonbranching_groups,
        *RM3.Rules.branching_groups,
        *KFDE.Rules.unmodal_groups,
        *RM3.Rules.unquantifying_groups)
