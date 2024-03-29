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

from itertools import chain

from ..tools import group
from . import cfol as CFOL
from . import kfde as KFDE


class Meta(CFOL.Meta):
    name = 'K'
    title = 'Kripke Normal Modal Logic'
    modal = True
    description = 'Base normal modal logic with no access relation restrictions'
    category_order = 1
    extension_of = (
        'CFOL',
        'KB3E',
        'KG3',
        'KK3',
        'KK3W',
        'KK3WQ',
        'KL3',
        'KLP',
        'KRM3')

class Model(CFOL.Model): pass
class System(CFOL.System): pass

class Rules(CFOL.Rules):

    class Possibility(KFDE.Rules.PossibilityDesignated): pass
    class PossibilityNegated(KFDE.Rules.PossibilityNegatedDesignated): pass
    class Necessity(KFDE.Rules.NecessityDesignated): pass
    class NecessityNegated(KFDE.Rules.NecessityNegatedDesignated): pass

    nonbranching_groups = group(
        group(
            *chain(*CFOL.Rules.nonbranching_groups),
            PossibilityNegated,
            NecessityNegated))

    unmodal_groups = group(
        group(
            Necessity,
            Possibility))

    groups = (
        *nonbranching_groups,
        *CFOL.Rules.branching_groups,
        *unmodal_groups,
        *CFOL.Rules.unquantifying_groups)
