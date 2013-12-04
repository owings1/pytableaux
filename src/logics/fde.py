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
    def build_trunk(tableau):
        branch = tableau.branch()
        for sentence in tableau.argument.premises:
            branch.add({ 'sentence': sentence, 'designated': True })
        branch.add({'sentence': tableau.argument.conclusion, 'designated': False })