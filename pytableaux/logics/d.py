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

from ..models import SerialAccess
from ..proof import rules
from ..tools import group
from . import k as K


class Meta(K.Meta):
    name = 'D'
    title = 'Deontic Normal Modal Logic'
    description = 'Normal modal logic with a serial access relation'
    category_order = 2
    extension_of = ('K')

class Model(K.Model):
    Access = SerialAccess

class System(K.System): pass

class Rules(K.Rules):

    Serial = rules.access.Serial

    groups = (
        *K.Rules.nonbranching_groups,
        *K.Rules.unmodal_groups,
        *K.Rules.branching_groups,
        *K.Rules.unquantifying_groups,
        group(Serial))
