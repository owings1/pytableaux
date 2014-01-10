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
    import k3, lp
    args = k3.example_invalidities()
    args.update(lp.example_invalidities())
    return args
    
import logic
from logic import negate, quantify

class TableauxSystem(logic.TableauxSystem):

    @staticmethod
    def build_trunk(tableau, argument):
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise, 'designated': True })
        branch.add({ 'sentence': argument.conclusion, 'designated': False })
        
class TableauxRules:

    NodeRule = logic.TableauxSystem.NodeRule
    OperatorDesignationRule = logic.TableauxSystem.OperatorDesignationRule
    DoubleOperatorDesignationRule = logic.TableauxSystem.DoubleOperatorDesignationRule
    
    class Closure(logic.TableauxSystem.ClosureRule):
    
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 
                    'sentence': node.props['sentence'], 
                    'designated': not node.props['designated'] 
                }): return branch
            return False

    class ConjunctionDesignated(OperatorDesignationRule):
        
        conditions = ('Conjunction', True)
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand, 'designated': True })
            branch.tick(node)

    class DisjunctionDesignated(OperatorDesignationRule):
        
        conditions = ('Disjunction', True)
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': operand, 
                    'designated': True 
                }).tick(node)
    
    class MaterialConditionalDesignated(OperatorDesignationRule):
        
        conditions = ('Material Conditional', True)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).add({ 
                'sentence': negate(sentence.lhs), 
                'designated': True 
            }).tick(node)
            self.tableau.branch(branch).add({ 
                'sentence': sentence.rhs, 
                'designated': True 
            }).tick(node)
            
    class MaterialBiconditionalDesignated(OperatorDesignationRule):

        conditions = ('Material Biconditional', True)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.lhs), 'designated': True },
                { 'sentence': negate(sentence.rhs), 'designated': True }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': sentence.rhs, 'designated': True },
                { 'sentence': sentence.lhs, 'designated': True }
            ]).tick(node)

    class ConditionalDesignated(MaterialConditionalDesignated):
        
        conditions = ('Conditional', True)
                    
    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        
        conditions = ('Biconditional', True)
                    
    class UniversalDesignated(logic.TableauxSystem.BranchRule):

        def applies_to_branch(self, branch):
            constants = branch.constants()
            for node in branch.get_nodes():
                if node.props['sentence'].quantifier == 'Universal' and node.props['designated']:
                    variable = node.props['sentence'].variable
                    if len(constants):
                        for constant in constants:
                            sentence = node.props['sentence'].sentence.substitute(constant, variable)
                            if not branch.has({ 'sentence': sentence, 'designated': True }):
                                return { 'branch': branch, 'sentence': sentence }
                    else:
                        constant = branch.new_constant()
                        sentence = node.props['sentence'].sentence.substitute(constant, variable)
                        return { 'branch': branch, 'sentence': sentence }
            return False

        def apply(self, target):
            target['branch'].add({ 'sentence': target['sentence'], 'designated': True })
            
    class ExistentialDesignated(NodeRule):

        def applies_to_node(self, node, branch):
            return (node.props['designated'] and
                    node.props['sentence'].quantifier == 'Existential')

        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].sentence
            variable = node.props['sentence'].variable
            branch.add({ 
                'sentence': sentence.substitute(branch.new_constant(), variable),
                'designated': True 
            }).tick(node)
                    
    class ConjunctionUndesignated(OperatorDesignationRule):
        
        conditions = ('Conjunction', False)
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 
                    'sentence': operand, 
                    'designated': False 
                }).tick(node)

    class DisjunctionUndesignated(OperatorDesignationRule):
        
        conditions = ('Disjunction', False)
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                branch.add({ 'sentence': operand, 'designated': False })
            branch.tick(node)
    
    class MaterialConditionalUndesignated(OperatorDesignationRule):
        
        conditions = ('Material Conditional', False)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            branch.update([
                { 'sentence': negate(sentence.lhs), 'designated': False },
                { 'sentence': sentence.rhs, 'designated': False }
            ]).tick(node)
            
    class MaterialBiconditionalUndesignated(OperatorDesignationRule):

        conditions = ('Material Biconditional', False)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence']
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.lhs), 'designated': False },
                { 'sentence': sentence.rhs, 'designated': False }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.rhs), 'designated': False },
                { 'sentence': sentence.lhs, 'designated': False }
            ]).tick(node)
    
    class ConditionalUndesignated(MaterialConditionalUndesignated):
        
        conditions = ('Conditional', False)
                    
    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        
        conditions = ('Biconditional', False)
                    
    class UniversalUndesignated(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (not node.props['designated'] and
                    node.props['sentence'].quantifier == 'Universal')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].sentence
            variable = node.props['sentence'].variable
            branch.add({
                'sentence': sentence.substitute(branch.new_constant(), variable),
                'designated': False
            }).tick(node)
            
    class ExistentialUndesignated(logic.TableauxSystem.BranchRule):
        
        def applies_to_branch(self, branch):
            constants = branch.constants()
            for node in branch.get_nodes():
                if node.props['sentence'].quantifier == 'Existential' and not node.props['designated']:
                    variable = node.props['sentence'].variable
                    if len(constants):
                        for constant in constants:
                            sentence = node.props['sentence'].sentence.substitute(constant, variable)
                            if not branch.has({ 'sentence': sentence, 'designated': False }):
                                return { 'branch': branch, 'sentence': sentence }
                    else:
                        constant = branch.new_constant()
                        sentence = node.props['sentence'].sentence.substitute(constant, variable)
                        return { 'branch': branch, 'sentence': sentence }
            return False

        def apply(self, target):
            target['branch'].add({ 'sentence': target['sentence'], 'designated': False })
                
    class NegatedConjunctionDesignated(DoubleOperatorDesignationRule):
        
        conditions = (('Negation', 'Conjunction'), True)
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 
                    'sentence': negate(operand), 
                    'designated': True 
                }).tick(node)

    class NegatedDisjunctionDesignated(DoubleOperatorDesignationRule):
        
        conditions = (('Negation', 'Disjunction'), True)
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                branch.add({ 'sentence': negate(operand), 'designated': True })
            branch.tick(node)
    
    class NegatedMaterialConditionalDesignated(DoubleOperatorDesignationRule):
        
        conditions = (('Negation', 'Material Conditional'), True)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            branch.update([
                { 'sentence': sentence.lhs, 'designated': True },
                { 'sentence': negate(sentence.rhs), 'designated': True }
            ]).tick(node)
            
    class NegatedMaterialBiconditionalDesignated(DoubleOperatorDesignationRule):

        conditions = (('Negation', 'Material Biconditional'), True)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).update([
                { 'sentence': sentence.lhs, 'designated': True },
                { 'sentence': negate(sentence.rhs), 'designated': True }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': sentence.rhs, 'designated': True },
                { 'sentence': negate(sentence.lhs), 'designated': True }
            ]).tick(node)

    class NegatedConditionalDesignated(NegatedMaterialConditionalDesignated):
        
        conditions = (('Negation', 'Conditional'), True)
                    
    class NegatedBiconditionalDesignated(NegatedMaterialBiconditionalDesignated):
        
        conditions = (('Negation', 'Biconditional'), True)
                    
    class DoubleNegationDesignated(DoubleOperatorDesignationRule):
    
        conditions = (('Negation', 'Negation'), True)
                    
        def apply_to_node(self, node, branch):
            branch.add({ 
                'sentence': node.props['sentence'].operand.operand,
                'designated': True
            }).tick(node)
            
    class NegatedConjunctionUndesignated(DoubleOperatorDesignationRule):
        
        conditions = (('Negation', 'Conjunction'), False)
                
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                branch.add({ 
                    'sentence': negate(operand), 
                    'designated': False 
                }).tick(node)

    class NegatedDisjunctionUndesignated(DoubleOperatorDesignationRule):
        
        conditions = (('Negation', 'Disjunction'), False)
            
        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 
                    'sentence': negate(operand), 
                    'designated': False 
                }).tick(node)
    
    class NegatedMaterialConditionalUndesignated(DoubleOperatorDesignationRule):
        
        conditions = (('Negation', 'Material Conditional'), False)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).add({ 
                'sentence': sentence.lhs, 
                'designated': False 
            }).tick(node)
            self.tableau.branch(branch).add({ 
                'sentence': negate(sentence.rhs), 
                'designated': False
            }).tick(node)
            
    class NegatedMaterialBiconditionalUndesignated(DoubleOperatorDesignationRule):

        conditions = (('Negation', 'Material Biconditional'), False)
            
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand
            self.tableau.branch(branch).update([
                { 'sentence': negate(sentence.lhs), 'designated': False },
                { 'sentence': negate(sentence.rhs), 'designated': False }
            ]).tick(node)
            self.tableau.branch(branch).update([
                { 'sentence': sentence.rhs, 'designated': False },
                { 'sentence': sentence.lhs, 'designated': False }
            ]).tick(node)
            
    class NegatedConditionalUndesignated(NegatedMaterialConditionalUndesignated):

        conditions = (('Negation', 'Conditional'), False)
                    
    class NegatedBiconditionalUndesignated(NegatedMaterialBiconditionalUndesignated):

        conditions = (('Negation', 'Biconditional'), False)
                    
    class DoubleNegationUndesignated(DoubleOperatorDesignationRule):

        conditions = (('Negation', 'Negation'), False)

        def apply_to_node(self, node, branch):
            branch.add({ 
                'sentence': node.props['sentence'].operand.operand,
                'designated': False
        }).tick(node)
    
    class NegatedUniversal(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and
                    sentence.operand.quantifier == 'Universal')
                    
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand.sentence
            variable = node.props['sentence'].operand.variable
            branch.add({ 
                'sentence': quantify('Existential', variable, negate(sentence)),
                'designated': node.props['designated'] 
            }).tick(node)
    
    class NegatedExistential(NodeRule):
        
        def applies_to_node(self, node, branch):
            sentence = node.props['sentence']
            return (sentence.operator == 'Negation' and
                    sentence.operand.quantifier == 'Existential')
        
        def apply_to_node(self, node, branch):
            sentence = node.props['sentence'].operand.sentence
            variable = node.props['sentence'].operand.variable
            branch.add({ 
                'sentence': quantify('Universal', variable, negate(sentence)),
                'designated': node.props['designated'] 
            }).tick(node)
        
    rules = [
        Closure,
        # non-branching rules
        ConjunctionDesignated, 
        DoubleNegationUndesignated, 
        MaterialConditionalUndesignated,
        ConditionalUndesignated, 
        NegatedDisjunctionDesignated,
        NegatedMaterialConditionalDesignated, 
        NegatedConditionalDesignated,
        DoubleNegationDesignated,
        NegatedDisjunctionUndesignated, 
        NegatedMaterialConditionalUndesignated,
        NegatedConditionalUndesignated,
        DoubleNegationUndesignated, 
        DisjunctionUndesignated,
        NegatedUniversal, 
        NegatedExistential, 
        ExistentialDesignated, 
        UniversalUndesignated,
        ExistentialUndesignated, 
        UniversalDesignated,
        # branching rules
        DisjunctionDesignated, 
        MaterialConditionalDesignated, 
        ConditionalDesignated,
        MaterialBiconditionalDesignated, 
        BiconditionalDesignated,
        ConjunctionUndesignated, 
        MaterialBiconditionalUndesignated, 
        BiconditionalUndesignated,
        NegatedConjunctionDesignated,
        NegatedMaterialBiconditionalDesignated, 
        NegatedBiconditionalDesignated,
        NegatedConjunctionUndesignated,
        NegatedMaterialBiconditionalUndesignated,
        NegatedBiconditionalUndesignated
    ]