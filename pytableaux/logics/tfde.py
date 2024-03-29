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

from ..tools import group
from . import kfde as KFDE
from . import t as T


class Meta(KFDE.Meta):
    name = 'TFDE'
    title = 'FDE with T modal'
    description = 'Modal version of FDE based on T normal modal logic'
    category_order = 3
    extension_of = ('KFDE')

class Model(KFDE.Model):
    Access = T.Model.Access

class System(KFDE.System): pass

class Rules(KFDE.Rules):

    Reflexive = T.Rules.Reflexive

    groups = (
        *KFDE.Rules.nonbranching_groups,
        *KFDE.Rules.unmodal_groups,
        group(Reflexive),
        *KFDE.Rules.branching_groups,
        *KFDE.Rules.unquantifying_groups)
