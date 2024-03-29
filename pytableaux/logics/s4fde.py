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
from . import s4 as S4
from . import tfde as TFDE


class Meta(TFDE.Meta):
    name = 'S4FDE'
    title = 'FDE with S4 modal'
    description = 'Modal version of FDE based on S4 normal modal logic'
    category_order = 4
    extension_of = ('TFDE')

class Model(TFDE.Model):
    Access = S4.Model.Access

class System(TFDE.System): pass

class Rules(TFDE.Rules):

    Transitive = S4.Rules.Transitive

    groups = (
        *TFDE.Rules.nonbranching_groups,
        group(Transitive),
        *TFDE.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *TFDE.Rules.branching_groups,
        *TFDE.Rules.unquantifying_groups)
