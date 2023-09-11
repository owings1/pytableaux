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

from . import k3 as K3
from . import s4fde as S4FDE


class Meta(K3.Meta, S4FDE.Meta):
    name = 'S4K3'
    title = 'K3 with S4 modal'
    description = 'Modal version of K3 based on S4 normal modal logic'
    category_order = 9
    extension_of = ('TK3', 'S4FDE')

class Model(K3.Model, S4FDE.Model): pass
class System(K3.System, S4FDE.System): pass
class Rules(K3.Rules, S4FDE.Rules): pass
