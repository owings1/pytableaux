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

from ..models import ReflexiveTransitiveAccesss
from ..proof import rules
from ..tools import group
from . import k as K
from . import t as T


class Meta(T.Meta):
    name = 'S4'
    title = 'S4 Normal Modal Logic'
    description = (
        'Normal modal logic with a reflexive and '
        'transitive access relation')
    category_order = 4
    extension_of = (
        'S4B3E',
        'S4G3',
        'S4GO',
        'S4K3',
        'S4K3W',
        'S4L3',
        'S4LP',
        'S4RM3',
        'T')

class Model(T.Model):
    Access: type[ReflexiveTransitiveAccesss] = ReflexiveTransitiveAccesss

class System(K.System): pass

class Rules(T.Rules):

    class Transitive(rules.access.Transitive): pass

    groups = (
        *K.Rules.nonbranching_groups,
        group(Transitive),
        *K.Rules.unmodal_groups,
        group(T.Rules.Reflexive),
        *K.Rules.branching_groups,
        *K.Rules.unquantifying_groups)
