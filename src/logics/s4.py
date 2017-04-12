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
# pytableaux - S4 Normal Modal Logic

name = 'S4'
description = 'S4 Normal Modal Logic'

def example_validities():
    import t
    args = t.example_validities()
    args.update([
		'S4 Conditional Inference 1' ,
		'S4 Material Inference 1'    ,
        'S4 Inference 1'             ,
    ])
    return args
    
def example_invalidities():
    args = set([
		'S5 Conditional Inference 1' ,
		'S5 Material Inference 1'    ,
	    'Possibility Distribution'   ,
        'Affirming a Disjunct 1'     ,
        'Affirming a Disjunct 2'     ,
        'Affirming the Consequent'   ,
        'Conditional Equivalence'    ,
        'Denying the Antecedent'     ,
        'Existential from Universal' ,
        'Extracting a Disjunct 1'    ,
        'Extracting a Disjunct 2'    ,
        'Extracting the Antecedent'  ,
        'Extracting the Consequent'  ,
        'Modal Transformation 1'     ,
        'Modal Transformation 2'     ,
        'Modal Transformation 3'     ,
        'Modal Transformation 4'     ,
        'NP Collapse 1'              ,
        'Triviality 1'               ,
        'Triviality 2'               ,
    ])
    return args
    
import logic, k, t

class TableauxSystem(k.TableauxSystem):
    pass
    
class TableauxRules(object):
    
    class Transitive(logic.TableauxSystem.BranchRule):
        
        def applies_to_branch(self, branch):
            nodes = {node for node in branch.get_nodes() if 'world1' in node.props}
            for node in nodes:
                for other_node in nodes:
                    if node.props['world2'] == other_node.props['world1']:
                        n = branch.find({ 
                            'world1': node.props['world1'], 
                            'world2': other_node.props['world2']
                        })
                        if n == None:
                            return { 
                                'world1': node.props['world1'],
                                'world2': other_node.props['world2'],
                                'branch': branch,
                                'nodes' : set([node, other_node])
                            }
            return False

        def apply(self, target):
            target['branch'].add({
                'world1': target['world1'],
                'world2': target['world2']
            })

        def example(self):
            self.tableau.branch().update([
                { 'world1' : 0, 'world2' : 1 },
                { 'world1' : 1, 'world2' : 2 }
            ])
    
    rules = list(t.TableauxRules.rules)
    rules.insert(2, Transitive)