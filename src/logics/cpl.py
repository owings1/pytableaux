name = 'CPL'
description = 'Classical Propositional Logic'

def example_validities():
    import fde
    args = fde.example_validities()
    args.update({
        'Disjunctive Syllogism'       : [['Aab', 'Nb'], 'a'],
        'Law of Excluded Middle'      : [[], 'AaNa'],
        'Law of Non-contradiction'    : [['KaNa'], 'b'],
        'Identity'                    : [[], 'Caa'],
        'Modus Ponens'                : [['Cab', 'a'], 'b'],
        'Modus Tollens'               : [['Cab', 'Nb'], 'Na'],
        'Pseudo Contraction'          : [[], 'CCaCabCab'],
        'Biconditional Elimination'   : [['Eab', 'a'], 'b'],
        'Biconditional Elimination 2' : [['Eab', 'Na'], 'Nb']
    })
    return args
    
def example_invalidities():
    return ({
        'Triviality 1'				: [['a'], 'b'],
        'Triviality 2'				: [[], 'a'],
        'Affirming the Consequent'	: [['Cab', 'b'], 'a'],
        'Affirming a Disjunct 1'	: [['Aab', 'a'], 'b'],
        'Affirming a Disjunct 2'	: [['Aab', 'a'], 'Nb'],
        'Conditional Equivalence'	: [['Cab'], 'Cba'],
        'Extracting the Consequent' : [['Cab'], 'b'],
        'Extracting the Antecedent' : [['Cab'], 'a'],
        'Extracting as Disjunct 1'	: [['Aab'], 'b'],
        'Extracting as Disjunct 2'	: [['AaNb'], 'Na'],
        'Denying the Antecedent' 	: [['Cab', 'Na'], 'b']
    })

import logic
from logic import negate

class TableauxSystem(logic.TableauxSystem):
        
    @staticmethod
    def build_trunk(tableau, argument):
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise })
        branch.add({ 'sentence': negate(argument.conclusion) })
        
class TableauxRules:
    
    NodeRule = logic.TableauxSystem.NodeRule
    
    class Closure(logic.TableauxSystem.ClosureRule):
    
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 'sentence': negate(node.props['sentence']) }):
                    return True
            return False

    class Conjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Conjunction'
                
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands:
                branch.add({ 'sentence': sentence })
            branch.tick(node)
    
    class Disjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Disjunction'
            
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence': sentence }).tick(node)
    
    class MaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Material Conditional'
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands
            self.tableau.branch(branch).add({ 'sentence': negate(operands[0]) }).tick(node)
            self.tableau.branch(branch).add({ 'sentence': operands[1] }).tick(node)
            
    class MaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Material Biconditional'
            
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[0]) }, 
                { 'sentence': negate(operands[1]) }]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': operands[1] }, 
                { 'sentence': operands[0] }]).tick(node)
    
    class DoubleNegation(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Negation')

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': node.props['sentence'].operands[0].operands[0] }).tick(node)

    class NegatedConjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Conjunction')
                    
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands[0].operands:
                self.tableau.branch(branch).add({ 'sentence': negate(sentence) }).tick(node)
            
    class NegatedDisjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Disjunction')
        
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands[0].operands:
                branch.add({ 'sentence' : negate(sentence) })
            branch.tick(node)
            
    class NegatedMaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Material Conditional')
                    
        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands[0].operands
            branch.update([
                { 'sentence': operands[0] }, 
                { 'sentence': negate(operands[1]) }
            ]).tick(node)
                  
    class NegatedMaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operands[0].operator == 'Material Biconditional')

        def apply_to_node(self, node, branch):
            operands = node.props['sentence'].operands[0].operands
            self.tableau.branch(branch).update([
                { 'sentence': operands[0] },
                { 'sentence': negate(operands[1]) }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(operands[1]) },
                { 'sentence': operands[0] }
            ]).tick(node)
    
    rules = [
        Closure,
        # non-branching rules
        DoubleNegation, Conjunction, NegatedDisjunction, NegatedMaterialConditional,
        # branching rules
        Disjunction, MaterialConditional, MaterialBiconditional, NegatedConjunction, NegatedMaterialBiconditional
    ]