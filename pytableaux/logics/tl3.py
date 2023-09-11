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
from . import kl3 as KL3
from . import l3 as L3
from . import tfde as TFDE


class Meta(L3.Meta, TFDE.Meta):
    name = 'TL3'
    title = 'L3 with T modal'
    description = 'Modal version of L3 based on T normal modal logic'
    category_order = 18
    extension_of = ('KL3')

class Model(L3.Model, TFDE.Model): pass
class System(L3.System, TFDE.System): pass

class Rules(L3.Rules, TFDE.Rules):
    groups = (
        # non-branching rules
        KL3.Rules.groups[0],
        # modal rules
        *KL3.Rules.unmodal_groups,
        # reflexive rule
        group(TFDE.Rules.Reflexive),
        # branching rules
        L3.Rules.groups[1],
        # quantifier rules
        *L3.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
