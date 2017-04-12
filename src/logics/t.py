# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
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
#
# ------------------
#
# pytableaux - Reflexive Normal Modal Logic
"""
Reflexive Modal Logic is an extension of K, with a *reflexive* accessibility relation,
which states that for every world *w*, *w* accesses *w* (itself).

Links
-----

- `Stanford Encyclopedia on Modal Logic`_

"""
name = 'T'
description = 'Reflexive Normal Modal Logic'

def example_validities():
    import d
    args = d.example_validities()
    args.update([
    	'NP Collapse 1'         ,
        'Necessity Elimination' ,
        'Possibility Addition'  ,
        'Reflexive Inference 1' ,
    ])
    return args
    
def example_invalidities():
    import s4
    args = s4.example_invalidities()
    args.update([
		'S4 Inference 1'             ,
        'S4 Conditional Inference 1' ,
        'S4 Material Inference 1'    ,
    ])
    return args

import logic, k
from logic import atomic

class TableauxSystem(k.TableauxSystem):
    """
    T's Tableaux System inherits directly from K's.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for T contain the rules for K, as well as an additional
    Reflexive rule, which operates on the accessibility relation for worlds.
    """

    class Reflexive(logic.TableauxSystem.NodeRule):
        """
        The Reflexive rule applies to an open branch *b* when there is a node *n*
        on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no node such that world1 and world2 is *w*, add a node to *b* where world1 and world2
        is *w*.
        """

        ticked = None

        def applies_to_node(self, node, branch):
            for world in node.worlds():
                if not branch.has({ 'world1': world, 'world2': world }):
                    return { 'world': world }
            return False
            
        def apply(self, target):
            target['branch'].add({ 'world1': target['world'], 'world2': target['world'] })

        def example(self):
            self.tableau.branch().add({ 'sentence' : atomic(0, 0), 'world' : 0 })
            
    rules = list(k.TableauxRules.rules)
    rules.insert(2, Reflexive)