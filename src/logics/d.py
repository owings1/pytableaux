name = 'D'
description = 'Deontic Normal Modal Logic'
links = {
    'Stanford Encyclopedia': 'http://plato.stanford.edu/entries/logic-deontic/'
}

def example_validities():
    import k
    args = k.example_validities()
    args.update({
        'Serial Inference 1': [[], 'CLaMa']
    })
    return args
    
def example_invalidities():
    import t
    args = t.example_invalidities()
    args.update({
    	'Reflexive Inference 1': [[], 'CLaa']
    })
    return args
    
import logic, k

class TableauxSystem(k.TableauxSystem):
    pass

class TableauxRules:
    
    class Serial(logic.TableauxSystem.BranchRule):
        
        def applies_to_branch(self, branch):
            if len(self.tableau.history) and self.tableau.history[-1]['rule'] == self:
                return False
            serial_worlds = {node.props['world1'] for node in branch.get_nodes() if 'world1' in node.props}
            worlds = TableauxSystem.get_worlds_on_branch(branch) - serial_worlds
            if len(worlds):
                return { 'branch': branch, 'world': worlds.pop() }
            return False
                
        def apply(self, target):
            target['branch'].add({ 
                'world1': target['world'], 
                'world2': TableauxSystem.get_new_world(target['branch'])
            })

    krules = k.TableauxRules
    
    rules = [
        krules.Closure,
        # non-branching rules
        krules.DoubleNegation, krules.Conjunction, krules.NegatedDisjunction,
        krules.NegatedMaterialConditional, krules.NegatedPossibility, 
        krules.NegatedNecessity,
        # branching rules
        krules.Disjunction, krules.MaterialConditional, krules.MaterialBiconditional, 
        krules.NegatedConjunction, krules.NegatedMaterialBiconditional,
        # modal rules
        krules.Possibility, krules.Necessity, Serial
    ]