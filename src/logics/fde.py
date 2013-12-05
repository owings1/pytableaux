import logic

name = 'FDE'
description = 'First Degree Entailment 4-valued logic'
links = {
    'Stanford Encyclopedia' : 'http://plato.stanford.edu/entries/logic-paraconsistent/'
}

def example_validities():
    return {
        'Addition'       : [['a'], 'Aab'],
        'Simplification' : [['Kab'], 'a'],
        'DeMorgan 1'     : [['NAab'], 'KNaNb'],
        'DeMorgan 2'     : [['NKab'], 'ANaNb'],
        'DeMorgan 3'     : [['KNaNb'], 'NAab'],
        'DeMorgan 4'     : [['ANaNb'], 'NKab'],
        'Contraction'    : [['CaCab'], 'Cab'],
    }

def example_invalidities():
    import cpl
    return cpl.example_invalidities()
    

class TableauxSystem(logic.TableauxSystem):

    @staticmethod
    def build_trunk(tableau, argument):
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise, 'designated': True })
        branch.add({ 'sentence': argument.conclusion, 'designated': False })
        
class TableauxRules:

    NodeRule = logic.TableauxSystem.NodeRule
    
    class Closure(logic.TableauxSystem.ClosureRule):
    
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 
                    'sentence': node.props['sentence'], 
                    'designated': not node.props['designated'] 
                }): return True
            return False

    class ConjunctionDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['designated'] and
                    node.props['sentence'].operator == 'Conjunction')
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand, 'designated': True })
            branch.tick(node)

    class DisjunctionDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['designated'] and 
                    node.props['sentence'].operator == 'Disjunction')
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': operand, 
                    'designated': True 
                }).tick(node)
    
    class MaterialConditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['designated'] and 
                    node.props['sentence'].operator == 'Material Conditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands
            self.tableau.branch(branch).add({ 
                'sentence': negate(operands[0]), 
                'designated': True 
            }).tick(node)
            self.tableau.branch(branch).add({ 
                'sentence': operands[1], 
                'designated': True 
            }).tick(node)
            
    class MaterialBiconditionalDesignated(NodeRule):

        def applies_to_node(self, node, branch):
            return (node.props['designated'] and 
                    node.props['sentence'].operator == 'Material Biconditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[0]), 'designated': True },
                { 'sentence': negate(operands[1]), 'designated': True }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': operands[1], 'designated': True },
                { 'sentence': operands[0], 'designated': True }
            ]).tick(node)

    class ConjunctionUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (not node.props['designated'] and 
                    node.props['sentence'].operator == 'Conjunction')
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': operand, 
                    'designated': False 
                }).tick(node)

    class DisjunctionUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (not node.props['designated'] and 
                    node.props['sentence'].operator == 'Disjunction')
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand, 'designated': False })
            branch.tick(node)
    
    class MaterialConditionalUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (not node.props['designated'] and 
                    node.props['sentence'].operator == 'Material Conditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands
            branch.update([
                { 'sentence': negate(operands[0]), 'designated': False },
                { 'sentence': operands[1], 'designated': False }
            ]).tick(node)
            
    class MaterialBiconditionalUndesignated(NodeRule):

        def applies_to_node(self, node, branch):
            return (not node.props['designated'] and 
                    node.props['sentence'].operator == 'Material Biconditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[0]), 'designated': False },
                { 'sentence': operands[1], 'designated': False }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[1]), 'designated': False },
                { 'sentence': operands[0], 'designated': False }
            ]).tick(node)
            
    class NegatedConjunctionDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Conjunction')
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands[0].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': negate(operand), 
                    'designated': True 
                }).tick(node)

    class NegatedDisjunctionDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Disjunction')
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands[0].operands:
                branch.add({ 'sentence': negate(operand), 'designated': True })
            branch.tick(node)
    
    class NegatedMaterialConditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Material Conditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands[0].operands
            branch.update([
                { 'sentence': operands[0], 'designated': True },
                { 'sentence': negate(operands[1]), 'designated': True }
            ]).tick(node)
            
    class NegatedMaterialBiconditionalDesignated(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Material Biconditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands[0].operands
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[0]), 'designated': True },
                { 'sentence': negate(operands[1]), 'designated': True }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': operands[1], 'designated': True },
                { 'sentence': operands[0], 'designated': True }
            ]).tick(node)

    class DoubleNegationDesignated(NodeRule):
    
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Negation')
                    
        def apply_to_node(self, node, branch):
            branch.add({ 
                'sentence': node.props['sentence'].operands[0].operands[0],
                'designated': True
            }).tick(node)
            
    class NegatedConjunctionUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (not node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Conjunction')
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands[0].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': operand, 
                    'designated': False 
                }).tick(node)

    class NegatedDisjunctionUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (not node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Disjunction')
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands[0].operands:
                branch.add({ 'sentence': operand, 'designated': False })
            branch.tick(node)
    
    class NegatedMaterialConditionalUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (not node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Material Conditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands[0].operands
            branch.update([
                { 'sentence': negate(operands[0]), 'designated': False },
                { 'sentence': operands[1], 'designated': False }
            ]).tick(node)
            
    class NegatedMaterialBiconditionalUndesignated(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (not node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Material Biconditional')
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands[0].operands
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[0]), 'designated': False },
                { 'sentence': operands[1], 'designated': False }
            ]).tick(node)
            self.tableau.branch(branch).updateh([
                { 'sentence': negate(operands[1]), 'designated': False },
                { 'sentence': operands[0], 'designated': False }
            ]).tick(node)
            
    class DoubleNegationUndesignated(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (not node.props['designated'] and 
                    sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Negation')

        def apply_to_node(self, node, branch):
            branch.add({ 
                'sentence': node.props['sentence'].operands[0].operands[0],
                'designated': False
        }).tick(node)
        
    rules = [
        Closure,
        # non-branching rules
        ConjunctionDesignated, DoubleNegationUndesignated, 
        MaterialConditionalUndesignated, NegatedDisjunctionDesignated,
        NegatedMaterialConditionalDesignated, DoubleNegationDesignated,
        NegatedDisjunctionUndesignated, NegatedMaterialConditionalUndesignated,
        DoubleNegationUndesignated, DisjunctionUndesignated,
        # branching rules
        DisjunctionDesignated, MaterialConditionalDesignated, 
        MaterialBiconditionalDesignated, ConjunctionUndesignated, 
        MaterialBiconditionalUndesignated, NegatedConjunctionDesignated,
        NegatedMaterialBiconditionalDesignated, NegatedConjunctionUndesignated,
        NegatedMaterialBiconditionalUndesignated
    ]