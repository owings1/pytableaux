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
from . import kk3w as KK3W
from . import tfde as TFDE


class Meta(KK3W.Meta, TFDE.Meta):
    name = 'TK3W'
    title = 'K3W with T modal'
    description = 'Modal version of K3W based on T normal modal logic'
    category_order = 28
    extension_of = ('KK3W')

class Model(KK3W.Model, TFDE.Model): pass
class System(KK3W.System, TFDE.System): pass

class Rules(KK3W.Rules, TFDE.Rules):

    groups = (
        *KK3W.Rules.nonbranching_groups,
        *KK3W.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *KK3W.Rules.branching_groups,
        *KK3W.Rules.unquantifying_groups)
