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