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

from ..models import GlobalAccess
from ..proof import rules
from ..tools import group
from . import s4 as S4


class Meta(S4.Meta):
    name = 'S5'
    title = 'S5 Normal Modal Logic'
    description = (
        'Normal modal logic with global access relation')
    category_order = S4.Meta.category_order + 1
    extension_of = (
        'S4',
        'S5B3E',
        'S5G3',
        'S5K3',
        'S5K3W',
        'S5K3WQ',
        'S5L3',
        'S5LP',
        'S5MH',
        'S5NH',
        'S5RM3')

class Model(S4.Model):
    Access: type[GlobalAccess] = GlobalAccess

class System(S4.System): pass

class Rules(S4.Rules):

    class Symmetric(rules.access.Symmetric): pass

    groups = (
        *S4.Rules.groups,
        group(Symmetric))
