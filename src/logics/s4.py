# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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
title = 'S4 Normal Modal Logic'
description = 'Normal modal logic with a reflexive and transitive access relation'
tags = set(['bivalent', 'modal', 'first-order'])
tags_list = list(tags)
    
import logic
from . import k, t

class Model(t.Model):

    def finish(self):
        while True:
            super(Model, self).finish()
            to_add = set()
            for w1 in self.frames:
                for w2 in self.visibles(w1):
                    for w3 in self.visibles(w2):
                        a = (w1, w3)
                        if a not in self.access:
                            to_add.add(a)
            if len(to_add) == 0:
                return
            self.access.update(to_add)

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