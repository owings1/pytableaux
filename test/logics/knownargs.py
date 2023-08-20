from pytableaux.tools import qset, qsetf

validities = {}
invalidities = {}
validities[...] = qsetf([
    'Modal Platitude 1',
    'Modal Platitude 2',
    'Modal Platitude 3',
])
validities['FDE'] = validities[...] | [
        'Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',

        # 'Self Identity 1',
        'Simplification',
]
validities['K3'] = validities['FDE'] | [

]
validities['LP'] = validities['FDE'] | [
    
]
validities['RM3'] = validities['FDE'] | [
    
]
validities['L3'] = validities['FDE'] | [
    
]
validities['G3'] = validities[...] | [
    
]
validities['GO'] = validities[...] | [
    
]
validities['K3W'] = validities[...] | [
    
]
validities['K3WQ'] = validities[...] | [
    
]
validities['MH'] = validities[...] | [
    
]
validities['NH'] = validities[...] | [
    
]
validities['P3'] = validities[...] | [
    
]

validities['CPL'] = validities['FDE'] | [
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Identity',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism',
        'Disjunctive Syllogism 2',
        'Explosion',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Identity',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Identity',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Self Identity 1']

validities['CFOL'] = validities['CPL'] | [
        'Existential Syllogism',
        'Existential from Universal',
        'Self Identity 2',
        'Syllogism',
        'Universal Predicate Syllogism',
]
validities['K'] = validities['CFOL'] | [
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
]
validities['D'] = validities['K'] | [
        'Serial Inference 1',
        'Serial Inference 2',
]
validities['T'] = validities['D'] | [
        'NP Collapse 1',
        'Reflexive Inference 1',
]
validities['S4'] = validities['T'] | [
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
        'S4 Material Inference 2',
]
validities['S5'] = validities['S4'] | [
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
]



invalidities[...] = qsetf([
        'Triviality 1',
        'Triviality 2',
        'Affirming a Disjunct 1',
        'Affirming a Disjunct 2',
        'Affirming the Consequent',
        'Conditional Equivalence',
        'Denying the Antecedent',
        'Extracting a Disjunct 1',
        'Extracting a Disjunct 2',
        'Extracting the Antecedent',
        'Extracting the Consequent',
        'Universal from Existential'
])
invalidities['S5'] = invalidities[...] | [
]

invalidities['S4'] = invalidities['S5'] | [

]
invalidities['T'] = invalidities['S4'] | [

]
invalidities['D'] = invalidities['S4'] | [

]
invalidities['K'] = invalidities['T'] | [

]
invalidities['CFOL'] = invalidities['K'] | [

]
invalidities['CPL'] = qsetf([
        'Existential Syllogism',
        'Existential from Universal',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'NP Collapse 1',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
        'Necessity Elimination',
        'Possibility Addition',
        'Possibility Distribution',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Reflexive Inference 1',
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
        'S4 Material Inference 2',
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
        'Self Identity 2',
        'Serial Inference 1',
        'Serial Inference 2',
        'Syllogism',
        'Universal Predicate Syllogism',])


invalidities['K3'] = invalidities[...] | [

]
invalidities['LP'] = invalidities[...] | [
    
]
invalidities['RM3'] = invalidities[...] | [
    
]
invalidities['L3'] = invalidities[...] | [
    
]
invalidities['G3'] = invalidities[...] | [
    
]
invalidities['GO'] = invalidities[...] | [
    
]
invalidities['K3W'] = invalidities[...] | [
    
]
invalidities['K3WQ'] = invalidities[...] | [
    
]
invalidities['MH'] = invalidities[...] | [
    
]
invalidities['NH'] = invalidities[...] | [
    
]
invalidities['P3'] = invalidities[...] | [
    
]