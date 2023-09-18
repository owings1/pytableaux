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
from . import tk3wq as TK3WQ


class Meta(TK3WQ.Meta, S4FDE.Meta):
    name = 'S4K3WQ'
    title = 'K3WQ with S4 modal'
    description = 'Modal version of K3WQ based on S4 normal modal logic'
    category_order = TK3WQ.Meta.category_order + 1
    extension_of = ('TK3WQ')

class Model(TK3WQ.Model, S4FDE.Model): pass
class System(TK3WQ.System, S4FDE.System): pass

class Rules(TK3WQ.Rules, S4FDE.Rules):

    groups = (
        *TK3WQ.Rules.nonbranching_groups,
        group(S4FDE.Rules.Transitive),
        *TK3WQ.Rules.unmodal_groups,
        group(TK3WQ.Rules.Reflexive),
        *TK3WQ.Rules.branching_groups,
        *TK3WQ.Rules.unquantifying_groups)
