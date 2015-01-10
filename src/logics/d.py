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