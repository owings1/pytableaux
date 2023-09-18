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
from . import kmh as KMH
from . import tfde as TFDE


class Meta(KMH.Meta, TFDE.Meta):
    name = 'TMH'
    title = 'MH with T modal'
    description = 'Modal version of MH based on T normal modal logic'
    category_order = KMH.Meta.category_order + 2
    extension_of = ('KMH')

class Model(KMH.Model, TFDE.Model): pass
class System(KMH.System, TFDE.System): pass

class Rules(KMH.Rules, TFDE.Rules):

    groups = (
        *KMH.Rules.nonbranching_groups,
        *KMH.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *KMH.Rules.branching_groups,
        *KMH.Rules.unquantifying_groups)
