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

from ..proof import adds, sdwnode, sdwgroup, anode
from ..tools import group
from . import k3wq as K3WQ
from . import kfde as KFDE


class Meta(K3WQ.Meta, KFDE.Meta):
    name = 'KK3WQ'
    title = 'K3WQ with K modal'
    description = 'Modal version of K3WQ based on K normal modal logic'
    category_order = 30.1
    extension_of = ('K3WQ')

class Model(K3WQ.Model, KFDE.Model):

    def value_of_operated(self, s, /, **kw):
        self._check_finished()
        oper = s.operator
        if oper not in self.Meta.modal_operators:
            return super().value_of_operated(s, **kw)
        it = self._unmodal_values(s, **kw)
        # initial is least for Possibility, greatest for Necessity
        initial = self.valseq[oper.Possibility.index - oper.index]
        return self.truth_function.generalize(oper, it, initial)

class System(K3WQ.System, KFDE.System): pass

class Rules(K3WQ.Rules, KFDE.Rules):

    class PossibilityDesignated(KFDE.Rules.PossibilityDesignated):
        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            o = s.operator
            si = s.lhs
            if self.new_negated(self.negated):
                so = si
                si = ~si
            else:
                so = ~si
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(
                    sdwnode(o.Necessity(si | so), d, w1),
                    sdwnode(si, d, w2),
                    anode(w1, w2)),
                designated=d,
                sentence=si)

    class PossibilityUndesignated(KFDE.Rules.PossibilityDesignated):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            o = s.operator
            si = s.lhs
            if self.new_negated(self.negated):
                so = si
                si = ~si
            else:
                so = ~si
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(
                    sdwnode(si, d, w2),
                    sdwnode(so, d, w2),
                    anode(w1, w2)),
                sdwgroup((o.Necessity(so), not d, w1)),
                designated=d,
                sentence=si)

    class PossibilityNegatedUndesignated(KFDE.Rules.PossibilityDesignated):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            si = s.lhs
            if self.new_negated(self.negated):
                si = ~si
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(
                    sdwnode(si, d, w2),
                    anode(w1, w2)),
                designated=d,
                sentence=si)

    class NecessityNegatedDesignated(PossibilityDesignated):
        pass

    #     def _get_node_targets(self, node, branch, /):
    #         s = self.sentence(node)
    #         v = s.variable
    #         si = s.sentence
    #         d = self.designation
    #         w = node.get('world')
    #         yield adds(
    #             sdwgroup(
    #                 (self.quantifier(v, si | ~si), d, w),
    #                 (~(branch.new_constant() >> s), d, w)))

    class NecessityNegatedUndesignated(PossibilityUndesignated):
        pass

    #     def _get_node_targets(self, node, branch, /):
    #         s = self.sentence(node)
    #         v = s.variable
    #         si = s.sentence
    #         r = branch.new_constant() >> s
    #         d = self.designation
    #         w = node.get('world')
    #         yield adds(
    #             sdwgroup((r, d, w), (~r, d, w)),
    #             sdwgroup((self.quantifier(v, si), not d, w)))

    unmodal_groups = (
        group(
            KFDE.Rules.NecessityDesignated,
            KFDE.Rules.PossibilityNegatedDesignated),
        group(
            KFDE.Rules.NecessityUndesignated,
            PossibilityDesignated,
            PossibilityNegatedUndesignated,
            # KFDE.Rules.NecessityNegatedUndesignated,
            # KFDE.Rules.NecessityNegatedDesignated,
            NecessityNegatedDesignated,
            ),
        group(
            PossibilityUndesignated,
            NecessityNegatedUndesignated,
        ))

    groups = (
        *K3WQ.Rules.nonbranching_groups,
        *K3WQ.Rules.branching_groups,
        *unmodal_groups,
        *K3WQ.Rules.unquantifying_groups)
