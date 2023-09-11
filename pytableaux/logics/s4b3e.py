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
from . import b3e as B3E
from . import kb3e as KB3E
from . import s4fde as S4FDE
from . import tb3e as TB3E


class Meta(B3E.Meta, S4FDE.Meta):
    name = 'S4B3E'
    title = 'B3E with S4 modal'
    description = 'Modal version of B3E based on S4 normal modal logic'
    category_order = 34
    extension_of = ('TB3E')

class Model(B3E.Model, S4FDE.Model): pass
class System(B3E.System, S4FDE.System): pass

class Rules(TB3E.Rules):

    Transitive = S4FDE.Rules.Transitive

    groups = (
        # non-branching rules
        KB3E.Rules.groups[0],
        group(Transitive),
        *KB3E.Rules.unmodal_groups,
        group(TB3E.Rules.Reflexive),
        # branching rules
        *B3E.Rules.groups[1:4],
        *B3E.Rules.unquantifying_groups)
