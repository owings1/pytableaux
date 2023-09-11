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
from . import rm3 as RM3
from . import s4rm3 as S4RM3
from . import s5fde as S5FDE


class Meta(RM3.Meta, S5FDE.Meta):
    name = 'S5RM3'
    title = 'RM3 with S5 modal'
    description = 'Modal version of RM3 based on S5 normal modal logic'
    category_order = 25
    extension_of = ('S4RM3')

class Model(RM3.Model, S5FDE.Model): pass
class System(RM3.System, S5FDE.System): pass

class Rules(S4RM3.Rules):

    Symmetric = S5FDE.Rules.Symmetric

    groups = (
        *S4RM3.Rules.groups,
        group(Symmetric))
