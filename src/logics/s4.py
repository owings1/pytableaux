name = 'S4'
description = 'S4 Normal Modal Logic'

def example_validities():
    import t
    args = t.example_validities()
    args.update({
		'S4 Material Inference 1'    : 'CLaLLa',
		'S4 Conditional Inference 1' : 'ULaLLa'		
    })
    return args
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update({
	    'Possibility distribution'   : [['KMaMb'], 'MKab'],
		'S5 Material Inference 1'    : 'CaLMa',
		'S5 Conditional Inference 1' : 'UaLMa'
    })
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
                    if (node.props['world2'] == other_node.props['world1'] and
                        not branch.has({ 
                            'world1': node.props['world1'], 
                            'world2': other_node.props['world2']
                        })):
                            return { 
                                'world1': node.props['world1'],
                                'world2': other_node.props['world2'],
                                'branch': branch
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