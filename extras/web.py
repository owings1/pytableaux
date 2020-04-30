# deleted scenes from App class

    # this is a work in progress
    def prove(self, data):
        input_data = {
            'parser' : '',         # standard, polish
            'output' : {
                'formats'    : [], # list of logic names (fde, cfol, etc.)
                'notation'   : '', # optional, default is parser.notation
            },
            'predicates' : {
                'name' : {
                    'index'     : 0,
                    'subscript' : 0,
                    'arity'     : 1
                }
            },
            'argument' : {
                'premises'   : [], # None or missing is allowed
                'conclusion' : ''
            },
            'logics' : []
        }
        output_data = {
            'argument' : {
                'symbol_set' : {
                    'premises'   : [],
                    'conclusion' : ''
                }
            },
            'predicate_strings' : {     # includes system predicates
                'symbol_set' : {
                    'name' : ''
                }
            },
            'predicate_defs' : {            # includes system predicates
                'name' : {
                    'index'     : 0,
                    'subscript' : 0,
                    'arity'     : 1
                }
            },
            'headers' : {
                'format' : ''
            },
            'footers' : {
                'format' : ''
            },
            'proofs' : {
                'logicName' : {
                    'valid' : None,
                    'output' : {
                        'format' : ''
                    }
                }
            }
        }
        return output_data