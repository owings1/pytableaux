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
from . import LogicType
from . import fde as FDE
from . import k3 as K3
from . import kk3w as KK3W
from . import k3w as K3W
from . import s4k3w as S4K3W
from . import s5 as S5
from . import s5fde as S5FDE


class Meta(KK3W.Meta):
    name = 'S5K3W'
    title = 'K3W with S5 modal'
    description = 'Modal version of K3W based on S5 normal modal logic'
    category_order = 30
    extension_of = ('S4K3W')

class Model(S5FDE.Model, K3W.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = K3.Rules.closure
    groups = (
        *S4K3W.Rules.groups,
        group(S5.Rules.Symmetric))
