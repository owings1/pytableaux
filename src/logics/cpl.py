import logic, fde
Node = logic.TableauxSystem.Node

name = 'CPL'
description = 'Classical Propositional Logic'
operators = fde.operators.copy()
example_validities = {
    'Disjunctive Syllogism'       : [['Aab', 'Nb'], 'a'],
    'Law of Excluded Middle'      : [[], 'AaNa'],
    'Law of Non-contradiction'    : [['KaNa'], 'b'],
    'Identity'                    : [[], 'Caa'],
    'Modus Ponens'                : [['Cab', 'a'], 'b'],
    'Modus Tollens'               : [['Cab', 'Nb'], 'Na'],
    'DeMorgan 1'                  : [['NAab'], 'KNaNb'],
    'DeMorgan 2'                  : [['NKab'], 'ANaNb'],
    'DeMorgan 3'                  : [['KNaNb'], 'NAab'],
    'DeMorgan 4'                  : [['ANaNb'], 'NKab'],
    'Contraction'                 : [['CaCab'], 'Cab'],
    'Pseudo Contraction'          : [[], 'CCaCabCab'],
    'Biconditional Elimination'   : [['Eab', 'a'], 'b'],
    'Biconditional Elimination 2' : [['Eab', 'Na'], 'Nb']
}

class TableauxSystem(logic.TableauxSystem):
        
    @staticmethod
    def build_trunk(tableau):
        branch = tableau.branch()
        for sentence in tableau.argument.premises:
            branch.add(Node({ 'sentence': sentence }))
        branch.add(Node({'sentence': logic.negate(tableau.argument.conclusion)}))
        
class TableauxRules:
    
    NodeRule = logic.TableauxSystem.NodeRule
    
    class Closure(logic.TableauxSystem.ClosureRule):
    
        def applies_to_branch(self, branch):
            for node in branch.nodes():
                if branch.has({ 'sentence': logic.negate(node.props['sentence']) }):
                    return True
            return False

    class DoubleNegation(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Negation' and
                    node.props['sentence'].operands[0].operator == 'Negation')
                    
        def apply_to_node(self, node, branch):
            branch.add(Node({ 'sentence': node.props['sentence'].operands[0].operands[0] })).tick(node)
        
    class Conjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Conjunction')
                
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands:
                branch.add(Node({ 'sentence' : sentence }))
            branch.tick(node)
    
    class Disjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Disjunction')
            
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands:
                branch.branch(Node({ 'sentence': sentence }), self.tableau).tick(node)
            self.tableau.branches.discard(branch)
    
    class MaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Material Conditional')
            
        def apply_to_node(self, node, branch):
            branch.branch(Node({ 'sentence': logic.negate(node.props['sentence'].operands[0] )}), self.tableau).tick(node)
            branch.branch(Node({ 'sentence': node.props['sentence'].operands[1] }), self.tableau).tick(node)
            self.tableau.branches.discard(branch)
            
    class MaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Material Biconditional')
            
        def apply_to_node(self, node, branch):
            branch.branch(Node({'sentence': logic.negate(node.props['sentence'].operands[0])}), self.tableau) \
                  .add(Node({'sentence' : logic.negate(node.props['sentence'].operands[1])})).tick(node)
            branch.branch(Node({'sentence' : node.props['sentence'].operands[1] }), self.tableau) \
                  .add(Node({'sentence' : node.props['sentence'].operands[0] })).tick(node)
            self.tableau.branches.discard(branch)
    
    class NegatedConjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Negation' and
                    node.props['sentence'].operands[0].operator == 'Conjunction')
                    
        def apply_to_node(self, node, branch):
            branch.branch(Node({'sentence': logic.negate(node.props['sentence'].operands[0])}), self.tableau).tick(node)
            branch.branch(Node({'sentence': logic.negate(node.props['sentence'].operands[1])}), self.tableau).tick(node)
            self.tableau.branches.discard(branch)
            
    class NegatedDisjunction(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Negation' and
                    node.props['sentence'].operands[0].operator == 'Disjunction')
        
        def apply_to_node(self, node, branch):
            for sentence in node.props['sentence'].operands:
                branch.add(Node({ 'sentence' : logic.negate(sentence) }))
            branch.tick(node)
            
    class NegatedMaterialConditional(NodeRule):
        
        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Negation' and
                    node.props['sentence'].operands[0].operator == 'Material Conditional')
                    
        def apply_to_node(self, node, branch):
            branch.add(Node({'sentence': node.props['sentence'].operands[0]})) \
                  .add(Node({'sentence': logic.negate(node.props['sentence'].operands[1])})).tick(node)
                  
    class NegatedMaterialBiconditional(NodeRule):

        def applies_to_node(self, node, branch):
            return (node.props['sentence'].operator == 'Negation' and
                    node.props['sentence'].operands[0].operator == 'Material Biconditional')

        def apply_to_node(self, node, branch):
            branch.branch(Node({'sentence': node.props['sentence'].operands[0]}), self.tableau) \
                  .add(Node({'sentence' : logic.negate(node.props['sentence'].operands[1])})).tick(node)
            branch.branch(Node({'sentence' : logic.negate(node.props['sentence'].operands[1])}), self.tableau) \
                  .add(Node({'sentence' : node.props['sentence'].operands[0] })).tick(node)
            self.tableau.branches.discard(branch)
    
    rules = [
        Closure,
        DoubleNegation,
        Conjunction,
        Disjunction,
        MaterialConditional,
        MaterialBiconditional,
        NegatedConjunction,
        NegatedDisjunction,
        NegatedMaterialConditional,
        NegatedMaterialBiconditional
    ]