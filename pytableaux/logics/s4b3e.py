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
from . import s4fde as S4FDE
from . import tb3e as TB3E


class Meta(TB3E.Meta, S4FDE.Meta):
    name = 'S4B3E'
    title = 'B3E with S4 modal'
    description = 'Modal version of B3E based on S4 normal modal logic'
    category_order = 29
    extension_of = ('TB3E')

class Model(TB3E.Model, S4FDE.Model): pass
class System(TB3E.System, S4FDE.System): pass

class Rules(TB3E.Rules, S4FDE.Rules):

    groups = (
        *TB3E.Rules.nonbranching_groups,
        group(S4FDE.Rules.Transitive),
        *TB3E.Rules.unmodal_groups,
        group(TB3E.Rules.Reflexive),
        *TB3E.Rules.branching_groups,
        *TB3E.Rules.unquantifying_groups)
