name = 'K'
description = 'Kripke Normal Modal Logic'
links = {
    'Stanford Encyclopedia': 'http://plato.stanford.edu/entries/logic-modal/'
}

def example_validities():
    import cpl
    args = cpl.example_validities()
    args.update({
        'Modal Platitude 1': [['Ma'], 'Ma'],
		'Modal Platitude 2': [['La'], 'La'],
		'Modal Platitude 3': [['LMa'], 'LMa'],
		'Modal Transformation 1': [['La'], 'NMNa'],
		'Modal Transformation 2': [['NMNa'], 'La'],
		'Modal Transformation 3': [['NLa'], 'MNa'],
		'Modal Transformation 4': [['MNa'], 'NLa'],
        'Necessity Distribution': 'CLCabCLaLb'
    })
    return args
    
def example_invalidities():
    import t
    args = t.example_invalidities()
    args.update({
        'Possibility Addition': [['a'], 'Ma'],
    	'Necessity Elimination': [['La'], 'a'],
    	'Reflexive Inference 1': 'CLaa',
    	'Serial Inference 1': 'CLaMa'
    })
    return args

import logic
from logic import negate, operate

class TableauxSystem(logic.TableauxSystem):
        
    @staticmethod
    def build_trunk(tableau, argument):
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise, 'world': 0 })
        branch.add({ 'sentence': negate(argument.conclusion), 'world': 0 })
           
    @staticmethod
    def get_worlds_on_branch(branch):
        worlds = set()
        for node in branch.get_nodes():
            if 'world' in node.props:
                worlds.add(node.props['world'])
            if 'world1' in node.props:
                worlds.add(node.props['world1'])
            if 'world2' in node.props:
                worlds.add(node.props['world2'])
        return worlds

    @staticmethod
    def get_new_world(branch):
        worlds = TableauxSystem.get_worlds_on_branch(branch)
        if not len(worlds):
            return 0
        return max(worlds) + 1

class TableauxRules:
    
    NodeRule = logic.TableauxSystem.NodeRule
    BranchRule = logic.TableauxSystem.BranchRule
    
    class Closure(logic.TableauxSystem.ClosureRule):
    
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if 'sentence' in node.props  and branch.has({ 
                    'sentence': negate(node.props['sentence']), 
                    'world': node.props['world'] 
                }): return branch
            return False

    class Conjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return ('sentence' in node.props and 
                    node.props['sentence'].operator == 'Conjunction')
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand, 'world': node.props['world'] })
            branch.tick(node)
    
    class Disjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return ('sentence' in node.props and 
                    node.props['sentence'].operator == 'Disjunction')
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': operand, 
                    'world': node.props['world'] 
                }).tick(node)
    
    class MaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            return ('sentence' in node.props and 
                    node.props['sentence'].operator == 'Material Conditional')
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            world = node.props['world']
            self.tableau.branch(branch).add({ 
                'sentence': negate(sentence.lhs),
                'world': world
            }).tick(node)
            self.tableau.branch(branch).add({ 
                'sentence': sentence.rhs,
                'world': world
            }).tick(node)
            
    class MaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            return ('sentence' in node.props and 
                    node.props['sentence'].operator == 'Material Biconditional')
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            world = node.props['world']
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.lhs), 'world': world }, 
                { 'sentence': negate(sentence.rhs), 'world': world }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': sentence.rhs, 'world': world }, 
                { 'sentence': sentence.lhs, 'world': world }
            ]).tick(node)
    
    class DoubleNegation(NodeRule):

        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Negation')

        def apply_to_node(self, node, branch):
            branch.add({ 
                'sentence': node.props['sentence'].operand.operand,
                'world': node.props['world']
            }).tick(node)

    class NegatedConjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Conjunction')
                    
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 
                    'sentence': negate(operand),
                    'world': node.props['world']
                }).tick(node)
            
    class NegatedDisjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Disjunction')
        
        def apply_to_node(self, node, branch):
            world = node.props['world']
            for operand in node.props['sentence'].operand.operands:
                branch.add({ 'sentence' : negate(operand), 'world': world })
            branch.tick(node)
            
    class NegatedMaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Material Conditional')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            world = node.props['world']
            branch.update([
                { 'sentence': sentence.lhs, 'world': world }, 
                { 'sentence': negate(sentence.rhs), 'world': world }
            ]).tick(node)
                  
    class NegatedMaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Material Biconditional')

        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            world = node.props['world']
            self.tableau.branch(branch).update([
                { 'sentence': sentence.lhs, 'world': world },
                { 'sentence': negate(sentence.rhs), 'world': world }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.rhs), 'world': world },
                { 'sentence': sentence.lhs, 'world': world }
            ]).tick(node)
    
    class Possibility(NodeRule):
        
        def applies_to_node(self, node, branch):
            return ('sentence' in node.props and
                    node.props['sentence'].operator == 'Possibility')
            
        def apply_to_node(self, node, branch):
            world = TableauxSystem.get_new_world(branch)
            branch.update([
                { 'sentence': node.props['sentence'].operand, 'world': world },
                { 'world1': node.props['world'], 'world2': world }
            ]).tick(node)
            
    class Necessity(BranchRule):
        
        def applies_to_branch(self, branch):
            worlds = TableauxSystem.get_worlds_on_branch(branch)
            for node in branch.get_nodes(ticked=False):
                if 'sentence' not in node.props:
                    continue
                sentence = node.props['sentence']
                if sentence.operator == 'Necessity':
                    for world in worlds:
                        if (branch.has({ 'world1': node.props['world'], 'world2': world }) and
                            not branch.has({ 'sentence': sentence.operand, 'world': world })):
                            return { 'node': node, 'world': world, 'branch': branch }
            return False
            
        def apply(self, target):
            target['branch'].add({ 
                'sentence': target['node'].props['sentence'].operand, 
                'world': target['world'] 
            })
            
    class NegatedPossibility(NodeRule):
        
        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Possibility')
        
        def apply_to_node(self, node, branch):
            branch.add({
                'sentence': operate('Necessity', [negate(node.props['sentence'].operand.operand)]),
                'world': node.props['world']
            }).tick(node)
        
    class NegatedNecessity(NodeRule):
        
        def applies_to_node(self, node, branch):
            if 'sentence' not in node.props:
                return False
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Necessity')
        
        def apply_to_node(self, node, branch):
            branch.add({
                'sentence': operate('Possibility', [negate(node.props['sentence'].operand.operand)]),
                'world': node.props['world']
            }).tick(node)
        
    rules = [
        Closure,
        # non-branching rules
        DoubleNegation, Conjunction, NegatedDisjunction, NegatedMaterialConditional,
        NegatedPossibility, NegatedNecessity,
        # branching rules
        Disjunction, MaterialConditional, MaterialBiconditional, NegatedConjunction, 
        NegatedMaterialBiconditional,
        # modal rules
        Possibility, Necessity
    ]