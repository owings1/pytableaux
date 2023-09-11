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

from . import k3w as K3W
from . import kk3w as KK3W
from . import tfde as TFDE


class Meta(K3W.Meta, TFDE.Meta):
    name = 'TK3W'
    title = 'K3W with T modal'
    description = 'Modal version of K3W based on T normal modal logic'
    category_order = 28
    extension_of = ('KK3W')

class Model(K3W.Model, TFDE.Model): pass
class System(K3W.System, TFDE.System): pass

class Rules(K3W.Rules):
    groups = (
        # non-branching rules
        KK3W.Rules.groups[0],
        # modal rules
        *TFDE.Rules.unmodal_groups,
        # reflexive rule
        TFDE.Rules.groups[3],
        # branching rules
        *K3W.Rules.groups[1:3],
        # quantifier rules
        *K3W.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, -4, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
