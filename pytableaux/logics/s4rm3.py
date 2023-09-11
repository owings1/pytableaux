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
from . import krm3 as KRM3
from . import trm3 as TRM3
from . import rm3 as RM3


class Meta(RM3.Meta, S4FDE.Meta):
    name = 'S4RM3'
    title = 'RM3 with S4 modal'
    description = 'Modal version of RM3 based on S4 normal modal logic'
    category_order = 24
    extension_of = ('TRM3')

class Model(RM3.Model, S4FDE.Model): pass
class System(RM3.System, S4FDE.System): pass

class Rules(TRM3.Rules):

    Transitive = S4FDE.Rules.Transitive

    groups = (
        # non-branching rules
        KRM3.Rules.groups[0],
        group(Transitive),
        *KRM3.Rules.unmodal_groups,
        group(TRM3.Rules.Reflexive),
        # branching rules
        *RM3.Rules.groups[1:3],
        *RM3.Rules.unquantifying_groups)
