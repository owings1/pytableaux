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

name = 'T'
description = 'Reflexive Normal Modal Logic'
links = {
    'Stanford Encyclopedia': 'http://plato.stanford.edu/entries/logic-modal/'
}

def example_validities():
    import d
    args = d.example_validities()
    args.update({
        'Possibility Addition': [['a'], 'Ma'],
        'Necessity Elimination': [['La'], 'a'],
    	'NP Collapse 1': [['LMa'], 'Ma']
    })
    return args
    
def example_invalidities():
    import s4
    args = s4.example_invalidities()
    args.update({
		'S4 Inference 1': 'CLaLLa'
    })
    return args

import logic, k
from logic import atomic

class TableauxSystem(k.TableauxSystem):
    pass

class TableauxRules(object):

    class Reflexive(logic.TableauxSystem.BranchRule):
                    
        def applies_to_branch(self, branch):
            for world in branch.worlds():
                if not branch.has({ 'world1': world, 'world2': world }):
                    return { 'world': world, 'branch': branch }
            return False
            
        def apply(self, target):
            target['branch'].add({ 'world1': target['world'], 'world2': target['world'] })

        def example(self):
            self.tableau.branch().add({ 'sentence' : atomic(0, 0), 'world' : 0 })
            
    rules = list(k.TableauxRules.rules)
    rules.insert(1, Reflexive)