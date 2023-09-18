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

from ..models import ReflexiveAccess
from ..proof import rules
from ..tools import group
from . import k as K


class Meta(K.Meta):
    name = 'T'
    title = 'Reflexive Normal Modal Logic'
    description = 'Normal modal logic with a reflexive access relation'
    category_order = K.Meta.category_order + 2
    extension_of = (
        'D',
        'TB3E',
        'TG3',
        'TK3',
        'TK3W',
        'TK3WQ',
        'TL3',
        'TLP',
        'TMH',
        'TNH',
        'TRM3')

class Model(K.Model):
    Access: type[ReflexiveAccess] = ReflexiveAccess

class System(K.System): pass

class Rules(K.Rules):

    class Reflexive(rules.access.Reflexive): pass

    groups = (
        *K.Rules.nonbranching_groups,
        *K.Rules.unmodal_groups,
        group(Reflexive),
        *K.Rules.branching_groups,
        *K.Rules.unquantifying_groups)
