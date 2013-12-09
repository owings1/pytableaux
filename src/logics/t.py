name = 'T'
description = 'Reflexive Normal Modal Logic'
links = {
    'Stanford Encyclopedia': 'http://plato.stanford.edu/entries/logic-modal/'
}

import k

def example_validities():
    args = k.example_validities()
    args.update({
    	'Reflexive Inference 1': [[], 'CLaa'],
    	'Possibility Addition': [['a'], 'Ma'],
    	'Necessity Elimination': [['La'], 'a'],
    	'Serial Inference 1': [[], 'CLaMa']
    })
    return args
    
def example_invalidities():
    import cpl
    args = cpl.example_invalidities()
    args.update({
	    'Possibility distribution': [['KMaMb'], 'MKab']
    })
    return args
    
class TableauxSystem(k.TableauxSystem):
    pass

import logic

class TableauxRules(k.TableauxRules):

    class Reflexive(logic.TableauxSystem.BranchRule):
                    
        def applies_to_branch(self, branch):
            for world in TableauxSystem.get_worlds_on_branch(branch):
                if not branch.has({ 'world1': world, 'world2': world }):
                    return { 'world': world, 'branch': branch }
            return False
            
        def apply(self, target):
            target['branch'].add({ 'world1': target['world'], 'world2': target['world'] })
            
    krules = k.TableauxRules    
    
    rules = [
        krules.Closure,
        Reflexive,
        # non-branching rules
        krules.DoubleNegation, krules.Conjunction, krules.NegatedDisjunction,
        krules.NegatedMaterialConditional, krules.NegatedPossibility, 
        krules.NegatedNecessity,
        # branching rules
        krules.Disjunction, krules.MaterialConditional, krules.MaterialBiconditional, 
        krules.NegatedConjunction, krules.NegatedMaterialBiconditional,
        # modal rules
        krules.Possibility, krules.Necessity
    ]