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

from . import b3e as B3E
from . import kfde as KFDE


class Meta(B3E.Meta, KFDE.Meta):
    name = 'KB3E'
    title = 'B3E with K modal'
    description = 'Modal version of B3E based on K normal modal logic'
    category_order = 31
    extension_of = ('B3E')

class Model(B3E.Model, KFDE.Model): pass
class System(B3E.System, KFDE.System): pass

class Rules(B3E.Rules, KFDE.Rules):

    groups = (
        *B3E.Rules.nonbranching_groups,
        *B3E.Rules.branching_groups,
        *KFDE.Rules.unmodal_groups,
        *B3E.Rules.unquantifying_groups)
