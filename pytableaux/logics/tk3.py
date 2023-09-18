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

from . import kk3 as KK3
from . import tfde as TFDE


class Meta(KK3.Meta, TFDE.Meta):
    name = 'TK3'
    title = 'K3 with T modal'
    description = 'Modal version of K3 based on T normal modal logic'
    category_order = KK3.Meta.category_order + 2
    extension_of = ('KK3', 'TFDE')

class Model(KK3.Model, TFDE.Model): pass
class System(KK3.System, TFDE.System): pass
class Rules(KK3.Rules, TFDE.Rules): pass
