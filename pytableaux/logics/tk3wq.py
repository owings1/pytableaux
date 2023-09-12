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
from . import kk3wq as KK3WQ
from . import tfde as TFDE


class Meta(KK3WQ.Meta, TFDE.Meta):
    name = 'TK3WQ'
    title = 'K3WQ with T modal'
    description = 'Modal version of K3WQ based on T normal modal logic'
    category_order = 30.3
    extension_of = ('KK3WQ')

class Model(KK3WQ.Model, TFDE.Model): pass
class System(KK3WQ.System, TFDE.System): pass

class Rules(KK3WQ.Rules, TFDE.Rules):

    groups = (
        *KK3WQ.Rules.nonbranching_groups,
        *KK3WQ.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *KK3WQ.Rules.branching_groups,
        *KK3WQ.Rules.unquantifying_groups)
