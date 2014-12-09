"""
CFOL - Classical First Order Logic.
"""

name = 'CFOL'
description = 'Classical First Order Logic'

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
        'Biconditional Elimination 2' : [['Eab', 'Na'], 'Nb'],
        'Syllogism'                   : [['VxCFxGx', 'VxCGxHx'], 'VxCFxHx']
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
        'Denying the Antecedent' 	: [['Cab', 'Na'], 'b'],
        'Existential from Universal': [['SxFx'], 'VxFx']
    }

import logic
from logic import negate, operate, quantify

class TableauxSystem(logic.TableauxSystem):
    
    @staticmethod
    def build_trunk(tableau, argument):
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise })
        branch.add({ 'sentence': negate(argument.conclusion) })
        
class TableauxRules:
    
    NodeRule = logic.TableauxSystem.NodeRule
    OperatorRule = logic.TableauxSystem.OperatorRule
    DoubleOperatorRule = logic.TableauxSystem.DoubleOperatorRule
    
    class Closure(logic.TableauxSystem.ClosureRule):
    
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 'sentence': negate(node.props['sentence']) }):
                    return branch
            return False

    class Conjunction(OperatorRule):
        
        operator = 'Conjunction'
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand })
            branch.tick(node)
    
    class Disjunction(OperatorRule):
        
        operator = 'Disjunction'
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence': operand }).tick(node)
    
    class Conditionals(NodeRule):
        
        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator in logic.conditional_operators
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).add({ 'sentence': negate(sentence.lhs) }).tick(node)
            self.tableau.branch(branch).add({ 'sentence': sentence.rhs }).tick(node)
            
    class Biconditionals(NodeRule):

        def applies_to_node(self, node, branch):
            return node.props['sentence'].operator in logic.biconditional_operators
            
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
                
    class DoubleNegation(DoubleOperatorRule):

        operators = ('Negation', 'Negation')

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': node.props['sentence'].operand.operand }).tick(node)

    class NegatedConjunction(DoubleOperatorRule):
        
        operators = ('Negation', 'Conjunction')
                    
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 'sentence': negate(operand) }).tick(node)
            
    class NegatedDisjunction(DoubleOperatorRule):
        
        operators = ('Negation', 'Disjunction')
        
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                branch.add({ 'sentence' : negate(operand) })
            branch.tick(node)
            
    class NegatedConditionals(DoubleOperatorRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator in logic.conditional_operators)
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            branch.update([
                { 'sentence': sentence.lhs }, 
                { 'sentence': negate(sentence.rhs) }
            ]).tick(node)
                  
    class NegatedBiconditionals(NodeRule):

        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and 
                    sentence.operand.operator in logic.biconditional_operators)

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
        DoubleNegation, Conjunction, NegatedDisjunction, NegatedConditionals,
        NegatedUniversal, NegatedExistential, Universal, Existential,
        # branching rules
        Disjunction, Conditionals, Biconditionals, NegatedConjunction, 
        NegatedBiconditionals
    ]