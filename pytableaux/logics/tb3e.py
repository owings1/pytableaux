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
from . import b3e as B3E
from . import kb3e as KB3E
from . import tfde as TFDE


class Meta(B3E.Meta, TFDE.Meta):
    name = 'TB3E'
    title = 'B3E with T modal'
    description = 'Modal version of B3E based on T normal modal logic'
    category_order = 33
    extension_of = ('KB3E')

class Model(B3E.Model, TFDE.Model): pass
class System(B3E.System, TFDE.System): pass

class Rules(B3E.Rules):

    Reflexive = TFDE.Rules.Reflexive

    groups = (
        # non-branching rules
        KB3E.Rules.groups[0],
        *KB3E.Rules.unmodal_groups,
        group(Reflexive),
        # branching rules
        *B3E.Rules.groups[1:4],
        *B3E.Rules.unquantifying_groups)
