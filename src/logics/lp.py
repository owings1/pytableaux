name = 'LP'
description = 'Logic of Paradox'

import fde

def example_validities():
    args = fde.example_validities()
    args.update({
        'Identity'                    : 'Caa',
        'Law of Excluded Middle'      : 'AaNa'
    })
    return args
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update({
        'Disjunctive Syllogism'       : [['Aab', 'Nb'], 'a'],
        'Law of Non-contradiction'    : [['KaNa'], 'b'],
        'Modus Ponens'                : [['Cab', 'a'], 'b'],
        'Modus Tollens'               : [['Cab', 'Nb'], 'Na']
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
                if not node.props['designated']:
                    if branch.has({
                        'sentence': negate(node.props['sentence']),
                        'designated': False
                    }):
                        return branch
            return False

    rules = list(fde.TableauxRules.rules)
    rules.insert(0, Closure)