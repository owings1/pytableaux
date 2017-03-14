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
# pytableaux - Deonitic Normal Modal Logic

"""
Deontic logic, also known as the Logic of Obligation, is an extension of K, with
a *serial* accessibility relation, which states that for every world *w*, there is
a world *w'* such that *w* accesses *w'*.

Links
-----

- `Stanford Encyclopedia on Deontic Logic`_

.. _Stanford Encyclopedia on Deontic Logic: http://plato.stanford.edu/entries/logic-deontic/

"""
name = 'D'
description = 'Deontic Normal Modal Logic'

def example_validities():
    import k
    args = k.example_validities()
    args.update({
        'Serial Inference 1': 'CLaMa'
    })
    return args
    
def example_invalidities():
    import t
    args = t.example_invalidities()
    args.update({
    	'Reflexive Inference 1' : 'CLaa',
        'Possibility Addition'  : [['a'], 'Ma'],
        'Necessity Elimination' : [['La'], 'a']
    })
    return args
    
import logic, k
from logic import atomic

class TableauxSystem(k.TableauxSystem):
    """
    D's Tableaux System inherits directly from K's.
    """
    pass

class TableauxRules:
    """
    The Tableaux Rules for D contain the rules for K, as well as an additional
    Serial rule, which operates on the accessibility relation for worlds.
    """
    class Serial(logic.TableauxSystem.BranchRule):
        """
        The Serial rule applies to a an open branch *b* when there is a world *w* that
        appears on *b*, but there is no world *w'* such that *w* accesses *w'*. The exception
        to this is when the Serial rule was the last rule to apply to the branch. This
        prevents infinite repetition of the Serial rule for open branches that are otherwise
        finished. For this reason, even though the Serial rule is non-branching, it is ordered
        last in the rules, so that all other rules are checked before it.

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no world *w'* on *b* such that *w* accesses *w'*, add a node to *b* with *w* as world1,
        and *w1* as world2, where *w1* does not yet appear on *b*.
        """
        
        def applies_to_branch(self, branch):
            if len(self.tableau.history) and self.tableau.history[-1]['rule'] == self:
                return False
            serial_worlds = {node.props['world1'] for node in branch.get_nodes() if 'world1' in node.props}
            worlds = branch.worlds() - serial_worlds
            if len(worlds):
                return { 'branch': branch, 'world': worlds.pop() }
            return False
                
        def apply(self, target):
            target['branch'].add({ 
                'world1': target['world'], 
                'world2': target['branch'].new_world()
            })

        def example(self):
            self.tableau.branch().add({ 'sentence' : atomic(0, 0), 'world' : 0 })

    rules = list(k.TableauxRules.rules)
    rules.append(Serial)