name = 'K3'
description = 'Strong Kleene 3-valued logic'

import fde

def example_validities():
    args = fde.example_validities()
    args.update({
        'Disjunctive Syllogism'       : [['Aab', 'Nb'], 'a'],
        'Law of Non-contradiction'    : [['KaNa'], 'b'],
        'Modus Ponens'                : [['Cab', 'a'], 'b'],
        'Modus Tollens'               : [['Cab', 'Nb'], 'Na']
    })
    return args
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update({
        'Identity'                    : 'Caa',
        'Law of Excluded Middle'      : 'AaNa'
    })
    return args
    
import logic
from logic import negate

class TableauxSystem(fde.TableauxSystem):
    pass
        
class TableauxRules:
    
    class Closure(logic.TableauxSystem.ClosureRule):
        
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if node.props['designated']:
                    if branch.has({
                        'sentence': negate(node.props['sentence']),
                        'designated': True
                    }):
                        return branch
            return False
    
    rules = list(fde.TableauxRules.rules)
    rules.insert(0, Closure)