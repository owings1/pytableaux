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
from . import kg3 as KG3
from . import tfde as TFDE


class Meta(KG3.Meta, TFDE.Meta):
    name = 'TG3'
    title = 'G3 with T modal'
    description = 'Modal version of G3 based on T normal modal logic'
    category_order = 38
    extension_of = ('KG3')

class Model(KG3.Model, TFDE.Model): pass
class System(KG3.System, TFDE.System): pass

class Rules(KG3.Rules, TFDE.Rules):

    groups = (
        *KG3.Rules.nonbranching_groups,
        *KG3.Rules.unmodal_groups,
        group(TFDE.Rules.Reflexive),
        *KG3.Rules.branching_groups,
        *KG3.Rules.unquantifying_groups)
