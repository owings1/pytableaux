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
from . import g3 as G3
from . import kg3 as KG3
from . import tfde as TFDE


class Meta(G3.Meta, TFDE.Meta):
    name = 'TG3'
    title = 'G3 with T modal'
    description = 'Modal version of G3 based on T normal modal logic'
    category_order = 38
    extension_of = ('KG3')

class Model(G3.Model, TFDE.Model): pass
class System(G3.System, TFDE.System): pass

class Rules(KG3.Rules):
    Reflexive = TFDE.Rules.Reflexive
    groups = (
        # non-branching rules
        KG3.Rules.groups[0],
        # modal rules
        *KG3.Rules.unmodal_groups,
        # reflexive rule
        group(Reflexive),
        # branching rules
        G3.Rules.groups[1],
        # quantifier rules
        *G3.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
