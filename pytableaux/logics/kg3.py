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

from . import g3 as G3
from . import kfde as KFDE


class Meta(G3.Meta, KFDE.Meta):
    name = 'KG3'
    title = 'G3 with K modal'
    description = 'Modal version of G3 based on K normal modal logic'
    category_order = 41
    extension_of = ('G3')

class Model(G3.Model, KFDE.Model): pass
class System(G3.System, KFDE.System): pass

class Rules(G3.Rules, KFDE.Rules):

    groups = (
        *G3.Rules.nonbranching_groups,
        *G3.Rules.branching_groups,
        *KFDE.Rules.unmodal_groups,
        *G3.Rules.unquantifying_groups)
