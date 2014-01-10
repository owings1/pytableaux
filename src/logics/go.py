name = 'GO'
description = 'Gappy Object 3-valued Logic'

def example_validities():
    return {
        'Addition'       : [['a'], 'Aab'],
        'Simplification' : [['Kab'], 'a'],
        'DeMorgan 3'     : [['KNaNb'], 'NAab'],
        'DeMorgan 4'     : [['ANaNb'], 'NKab'],
        'Contraction'    : [['CaCab'], 'Cab'],
    }
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update({
        'DeMorgan 1'     : [['NAab'], 'KNaNb'],
        'DeMorgan 2'     : [['NKab'], 'ANaNb'],
    })
    return args
    
import logic, fde, k3
from logic import negate, operate
    
class TableauxSystem(fde.TableauxSystem):
    pass
    
class TableauxRules(object):
    
    NodeRule = logic.TableauxSystem.NodeRule
    OperatorDesignationRule = logic.TableauxSystem.OperatorDesignationRule
    DoubleOperatorDesignationRule = logic.TableauxSystem.DoubleOperatorDesignationRule
    
    class UndesignatedCollapseRule(NodeRule):
        
        operator = None
        
        def applies_to_node(self, node, branch):
            return (not node.props['designated'] and
                    node.props['sentence'].operator == self.operator)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            branch.add({ 'sentence': negate(sentence), 'designated': True }).tick(node)
            
    class NegatedUndesignatedCollapseRule(NodeRule):
        
        operator = None
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (not node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == self.operator)
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            branch.add({ 'sentence': sentence, 'designated': True }).tick(node)
                
    class ConjunctionUndesignated(UndesignatedCollapseRule):
        operator = 'Conjunction'
    
    class NegatedConjunctionUndesignated(NegatedUndesignatedCollapseRule):
        operator = 'Conjunction'
        
    class DisjunctionUndesignated(UndesignatedCollapseRule):
        operator = 'Disjunction'
    
    class NegatedDisjunctionUndesignated(NegatedUndesignatedCollapseRule):
        operator = 'Disjunction'
        
    class MaterialConditionalUndesignated(UndesignatedCollapseRule):
        operator = 'Material Conditional'
        
    class NegatedMaterialConditionalUndesignated(NegatedUndesignatedCollapseRule):
        operator = 'Material Conditional'
        
    class MaterialBiconditionalUndesignated(UndesignatedCollapseRule):
        operator = 'Material Biconditional'
        
    class NegatedMaterialBiconditionalUndesignated(NegatedUndesignatedCollapseRule):
        operator = 'Material Biconditional'
        
    class ConditionalUndesignated(UndesignatedCollapseRule):
        operator = 'Conditional'
    
    class NegatedConditionalUndesignated(NegatedUndesignatedCollapseRule):
        operator = 'Conditional'
        
    class BiconditionalUndesignated(UndesignatedCollapseRule):
        operator = 'Biconditional'
        
    class NegatedBiconditionalUndesignated(NegatedUndesignatedCollapseRule):
        operator = 'Biconditional'
            
    class NegatedConjunctionDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == 'Conjunction')
        
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).add({
                'sentence': sentence.lhs,
                'designated': False
            }).tick(node)
            self.tableau.branch(branch).add({
                'sentence': sentence.rhs,
                'designated': False
            }).tick(node)
        
    class NegatedDisjunctionDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == 'Disjunction')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            branch.update([
                { 'sentence': sentence.lhs, 'designated': False },
                { 'sentence': sentence.rhs, 'designated': False }
            ]).tick(node)
    
    class NegatedMaterialConditionalDesignated(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == 'Material Conditional')

        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            branch.update([
                { 'sentence': negate(sentence.lhs), 'designated': False },
                { 'sentence': sentence.rhs, 'designated': False }
            ]).tick(node)
            
    class NegatedMaterialBiconditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == 'Material Biconditional')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.lhs), 'designated': False },
                { 'sentence': sentence.rhs, 'designated': False },
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.rhs), 'designated': False },
                { 'sentence': sentence.lhs, 'designated': False }
            ]).tick(node)
            
    class ConditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['designated'] and
                    node.props['sentence'].operator == 'Conditional')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).add({
                'sentence': operate('Disjunction', [negate(sentence.lhs), sentence.rhs]),
                'designated': True
            }).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': sentence.lhs, 'designated': False },
                { 'sentence': sentence.rhs, 'designated': False },
                { 'sentence': negate(sentence.lhs), 'designated': False },
                { 'sentence': negate(sentence.rhs), 'designated': False }
            ]).tick(node)

    class NegatedConditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == 'Conditional')
        
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).update([
                { 'sentence': sentence.lhs, 'designated': True },
                { 'sentence': sentence.rhs, 'designated': False }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.rhs), 'designated': True },
                { 'sentence': negate(sentence.lhs), 'designated': False }
            ]).tick(node)
            
    class BiconditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['designated'] and
                    node.props['sentence'].operator == 'Biconditional')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            branch.update([
                { 'sentence': operate('Conditional', [sentence.lhs, sentence.rhs]), 'designated': True },
                { 'sentence': operate('Conditional', [sentence.rhs, sentence.lhs]), 'designated': True }
            ]).tick(node)
            
    class NegatedBiconditionalDesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (node.props['designated'] and
                    sentence.operator == 'Negation' and
                    sentence.operand.operator == 'Biconditional')
        
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).add({
                'sentence': negate(operate('Conditional', [sentence.lhs, sentence.rhs])),
                'designated': True
            }).tick(node)
            self.tableau.branch(branch).add({
                'sentence': negate(operate('Conditional', [sentence.rhs, sentence.lhs])),
                'designated': True
            }).tick(node)
            
    fderules = fde.TableauxRules
    k3rules = k3.TableauxRules
    
    rules = [
        fderules.Closure,
        k3rules.Closure,
        fderules.ConjunctionDesignated,
        ConjunctionUndesignated,
        NegatedConjunctionUndesignated,
        NegatedDisjunctionDesignated,
        DisjunctionUndesignated,
        NegatedDisjunctionUndesignated,
        NegatedMaterialConditionalDesignated,
        MaterialConditionalUndesignated,
        NegatedMaterialConditionalUndesignated,
        MaterialBiconditionalUndesignated,
        NegatedMaterialBiconditionalUndesignated,
        ConditionalUndesignated,
        NegatedConditionalUndesignated,
        BiconditionalUndesignated,
        NegatedBiconditionalUndesignated,
        BiconditionalDesignated,
        
        # branching rules
        fderules.DisjunctionDesignated,
        NegatedConjunctionDesignated,
        fderules.MaterialConditionalDesignated,
        fderules.MaterialBiconditionalDesignated,
        NegatedMaterialBiconditionalDesignated,
        ConditionalDesignated,
        NegatedConditionalDesignated,
        NegatedBiconditionalDesignated
    ]