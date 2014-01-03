name = 'CPL'
description = 'Classical Propositional Logic'

def example_validities():
    import fde
    args = fde.example_validities()
    args.update({
        'Disjunctive Syllogism'       : [['Aab', 'Nb'], 'a'],
        'Law of Excluded Middle'      : 'AaNa',
        'Law of Non-contradiction'    : [['KaNa'], 'b'],
        'Identity'                    : 'Caa',
        'Modus Ponens'                : [['Cab', 'a'], 'b'],
        'Modus Tollens'               : [['Cab', 'Nb'], 'Na'],
        'Pseudo Contraction'          : 'CCaCabCab',
        'Biconditional Elimination'   : [['Eab', 'a'], 'b'],
        'Biconditional Elimination 2' : [['Eab', 'Na'], 'Nb']
    })
    return args
    
def example_invalidities():
    return {
        'Triviality 1'				: [['a'], 'b'],
        'Triviality 2'				: 'a',
        'Affirming the Consequent'	: [['Cab', 'b'], 'a'],
        'Affirming a Disjunct 1'	: [['Aab', 'a'], 'b'],
        'Affirming a Disjunct 2'	: [['Aab', 'a'], 'Nb'],
        'Conditional Equivalence'	: [['Cab'], 'Cba'],
        'Extracting the Consequent' : [['Cab'], 'b'],
        'Extracting the Antecedent' : [['Cab'], 'a'],
        'Extracting as Disjunct 1'	: [['Aab'], 'b'],
        'Extracting as Disjunct 2'	: [['AaNb'], 'Na'],
        'Denying the Antecedent' 	: [['Cab', 'Na'], 'b']
    }

import logic
from logic import negate, quantify

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
                    return branch
            return False

    class Conjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Conjunction'
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand })
            branch.tick(node)
    
    class Disjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Disjunction'
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence': operand }).tick(node)
    
    class MaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Material Conditional'
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).add({ 'sentence': negate(sentence.lhs) }).tick(node)
            self.tableau.branch(branch).add({ 'sentence': sentence.rhs }).tick(node)
            
    class MaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator == 'Material Biconditional'
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.lhs) }, 
                { 'sentence': negate(sentence.rhs) }]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': sentence.rhs }, 
                { 'sentence': sentence.lhs }]).tick(node)
    
    class Existential(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].quantifier == 'Existential'
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].sentence
            variable = node.props['sentence'].variable
            branch.add({ 'sentence': sentence.substitute(branch.new_constant(), variable) }).tick(node)
            
    class Universal(logic.TableauxSystem.BranchRule):
        
        def applies_to_branch(self, branch):
            constants = branch.constants()
            for node in branch.get_nodes():
                if node.props['sentence'].quantifier == 'Universal':
                    variable = node.props['sentence'].variable
                    if len(constants):
                        for constant in constants:
                            sentence = node.props['sentence'].sentence.substitute(constant, variable)
                            if not branch.has({ 'sentence': sentence }):
                                return { 'branch': branch, 'sentence': sentence }
                    else:
                        constant = branch.new_constant()
                        sentence = node.props['sentence'].sentence.substitute(constant, variable)
                        return { 'branch': branch, 'sentence': sentence }
            return False
            
        def apply(self, target):
            target['branch'].add({ 'sentence': target['sentence'] })
                
    class DoubleNegation(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Negation')

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': node.props['sentence'].operand.operand }).tick(node)

    class NegatedConjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Conjunction')
                    
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 'sentence': negate(operand) }).tick(node)
            
    class NegatedDisjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Disjunction')
        
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                branch.add({ 'sentence' : negate(operand) })
            branch.tick(node)
            
    class NegatedMaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Material Conditional')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            branch.update([
                { 'sentence': sentence.lhs }, 
                { 'sentence': negate(sentence.rhs) }
            ]).tick(node)
                  
    class NegatedMaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator == 'Material Biconditional')

        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).update([
                { 'sentence': sentence.lhs },
                { 'sentence': negate(sentence.rhs) }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.rhs) },
                { 'sentence': sentence.lhs }
            ]).tick(node)
    
    class NegatedExistential(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and
                    sentence.operand.quantifier == 'Existential')
        
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand.sentence
            variable = node.props['sentence'].operand.variable
            branch.add({ 'sentence': quantify('Universal', variable, negate(sentence)) }).tick(node)
            
    class NegatedUniversal(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and
                    sentence.operand.quantifier == 'Universal')
        
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand.sentence
            variable = node.props['sentence'].operand.variable
            branch.add({ 'sentence': quantify('Existential', variable, negate(sentence)) }).tick(node)
            
    rules = [
        Closure,
        # non-branching rules
        DoubleNegation, Conjunction, NegatedDisjunction, NegatedMaterialConditional,
        NegatedUniversal, NegatedExistential, Universal, Existential,
        # branching rules
        Disjunction, MaterialConditional, MaterialBiconditional, NegatedConjunction, 
        NegatedMaterialBiconditional
    ]