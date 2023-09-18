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
from . import kb3e as KB3E
from . import tfde as TFDE


class Meta(KB3E.Meta, TFDE.Meta):
    name = 'TB3E'
    title = 'B3E with T modal'
    description = 'Modal version of B3E based on T normal modal logic'
    category_order = KB3E.Meta.category_order + 2
    extension_of = ('KB3E')

class Model(KB3E.Model, TFDE.Model): pass
class System(KB3E.System, TFDE.System): pass

class Rules(KB3E.Rules, TFDE.Rules):

    groups = (
        *KB3E.Rules.nonbranching_groups,
        *KB3E.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *KB3E.Rules.branching_groups,
        *KB3E.Rules.unquantifying_groups)
