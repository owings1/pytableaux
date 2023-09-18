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

from . import s4fde as S4FDE
from . import tlp as TLP


class Meta(TLP.Meta, S4FDE.Meta):
    name = 'S4LP'
    title = 'LP with S4 modal'
    description = 'Modal version of LP based on S4 normal modal logic'
    category_order = TLP.Meta.category_order + 1
    extension_of = ('TLP', 'S4FDE')

class Model(TLP.Model, S4FDE.Model): pass
class System(TLP.System, S4FDE.System): pass
class Rules(TLP.Rules, S4FDE.Rules): pass
