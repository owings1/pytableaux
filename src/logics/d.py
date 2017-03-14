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
D - Deonitic Normal Modal Logic
"""
name = 'D'
description = 'Deontic Normal Modal Logic'
links = {
    'Stanford Encyclopedia': 'http://plato.stanford.edu/entries/logic-deontic/'
}

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
    	'Reflexive Inference 1': 'CLaa',
        'Possibility Addition': [['a'], 'Ma'],
        'Necessity Elimination': [['La'], 'a']
    })
    return args
    
import logic, k
from logic import atomic

class TableauxSystem(k.TableauxSystem):
    pass

class TableauxRules:
    
    class Serial(logic.TableauxSystem.BranchRule):
        
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