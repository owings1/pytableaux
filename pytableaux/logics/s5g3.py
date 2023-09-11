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
from . import s4g3 as S4G3
from . import s5fde as S5FDE


class Meta(S4G3.Meta, S5FDE.Meta):
    name = 'S5G3'
    title = 'G3 with S5 modal'
    description = 'Modal version of G3 based on S5 normal modal logic'
    category_order = 35
    extension_of = ('S4G3')

class Model(S4G3.Model, S5FDE.Model): pass
class System(S4G3.System, S5FDE.System): pass

class Rules(S4G3.Rules, S5FDE.Rules):

    groups = (
        *S4G3.Rules.groups,
        group(S5FDE.Rules.Symmetric))
