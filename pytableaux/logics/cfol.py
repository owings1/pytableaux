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
from . import LogicType
from . import cpl as CPL
from . import fde as FDE


class Meta(CPL.Meta):
    name = 'CFOL'
    title = 'Classical First Order Logic'
    quantified = True
    description = 'Standard bivalent logic with full first-order quantification'
    category_order = 2
    extension_of = (
        'B3E',
        'CPL',
        'G3',
        'GO',
        'K3',
        'K3W',
        'K3WQ',
        'LP',
        'L3',
        'MH',
        'NH',
        'RM3')

class Model(CPL.Model):
    value_of_quantified = FDE.Model.value_of_quantified

class System(CPL.System): pass

class Rules(LogicType.Rules):

    class Existential(FDE.Rules.ExistentialDesignated): pass
    class Universal(FDE.Rules.UniversalDesignated): pass
    class ExistentialNegated(FDE.Rules.ExistentialNegatedDesignated): pass
    class UniversalNegated(FDE.Rules.UniversalNegatedDesignated): pass

    unquantifying_groups = (
        group(
            Universal,
            ExistentialNegated),
        group(
            Existential,
            UniversalNegated))
    unquantifying_rules = tuple(chain(*unquantifying_groups))

    closure = CPL.Rules.closure
    groups = (
        *CPL.Rules.groups,
        *unquantifying_groups)
