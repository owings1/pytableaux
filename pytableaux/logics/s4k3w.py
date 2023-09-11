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
from . import k3w as K3W
from . import kk3w as KK3W
from . import s4fde as S4FDE
from . import tk3w as TK3W


class Meta(K3W.Meta, S4FDE.Meta):
    name = 'S4K3W'
    title = 'K3W with S4 modal'
    description = 'Modal version of K3W based on S4 normal modal logic'
    category_order = 29
    extension_of = ('TK3W')

class Model(K3W.Model, S4FDE.Model): pass
class System(K3W.System, S4FDE.System): pass

class Rules(TK3W.Rules):

    Transitive = S4FDE.Rules.Transitive

    groups = (
        # non-branching rules
        KK3W.Rules.groups[0],
        group(Transitive),
        *KK3W.Rules.unmodal_groups,
        group(TK3W.Rules.Reflexive),
        # branching rules
        *K3W.Rules.groups[1:3],
        # quantifier rules
        *K3W.Rules.unquantifying_groups)
