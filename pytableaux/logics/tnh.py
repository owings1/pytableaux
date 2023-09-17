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
from . import knh as KNH
from . import nh as NH
from . import tfde as TFDE


class Meta(NH.Meta, TFDE.Meta):
    name = 'TNH'
    title = 'NH with T modal'
    description = 'Modal version of NH based on T normal modal logic'
    category_order = 43
    extension_of = ('KNH')

class Model(NH.Model, TFDE.Model): pass
class System(NH.System, TFDE.System): pass

class Rules(KNH.Rules, TFDE.Rules):

    groups = (
        *KNH.Rules.nonbranching_groups,
        *KNH.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *KNH.Rules.branching_groups,
        *KNH.Rules.unquantifying_groups)
