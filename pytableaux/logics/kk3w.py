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
from . import k3w as K3W
from . import kfde as KFDE


class Meta(K3W.Meta, KFDE.Meta):
    name = 'KK3W'
    title = 'K3W with K modal'
    description = 'Modal version of K3W based on K normal modal logic'
    category_order = 26
    extension_of = ('K3W')

class Model(K3W.Model, KFDE.Model): pass
class System(K3W.System, KFDE.System): pass

class Rules(K3W.Rules, KFDE.Rules):
    groups = (
        K3W.Rules.groups[0] + group(
            # non-branching rules
            KFDE.Rules.PossibilityNegatedDesignated,
            KFDE.Rules.PossibilityNegatedUndesignated,
            KFDE.Rules.NecessityNegatedDesignated,
            KFDE.Rules.NecessityNegatedUndesignated),
        # branching rules
        *K3W.Rules.groups[1:3],
        *KFDE.Rules.unmodal_groups,
        *K3W.Rules.unquantifying_groups)

    @staticmethod
    def _check_groups():
        cls = __class__
        for branching, group in zip(range(3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
