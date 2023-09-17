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
from . import kmh as KMH
from . import mh as MH
from . import s4fde as S4FDE


class Meta(MH.Meta, S4FDE.Meta):
    name = 'S4MH'
    title = 'MH with S4 modal'
    description = 'Modal version of MH based on S4 normal modal logic'
    category_order = 49
    extension_of = ('TMH')

class Model(MH.Model, S4FDE.Model): pass
class System(MH.System, S4FDE.System): pass

class Rules(KMH.Rules, S4FDE.Rules):

    groups = (
        *KMH.Rules.nonbranching_groups,
        group(S4FDE.Rules.Transitive),
        *KMH.Rules.unmodal_groups,
        group(S4FDE.Rules.Reflexive),
        *KMH.Rules.branching_groups,
        *KMH.Rules.unquantifying_groups)
