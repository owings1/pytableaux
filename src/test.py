"""
Copyright (C) 2014, Doug Owings. All Rights Reserved.
"""

from logic import *

def main():
    test_all()
    
def test_all():
    test_logics()
    
def test_logics():
    from notations import polish
    from logics import fde, k3, lp, go, cfol, k, d, t, s4
    logics = [
        fde,
        k3,
        lp,
        go,
        cfol,
        k,
        d,
        t,
        s4
    ]
    vocabulary = Vocabulary()
    vocabulary.declare_predicate('is F', 0, 0, 1)
    vocabulary.declare_predicate('is G', 1, 0, 1)
    vocabulary.declare_predicate('is H', 2, 0, 1)
    parser = polish.Parser(vocabulary)
    for logic in logics:
        print logic.name
        print '  validities'
        test_arguments(logic, logic.example_validities(), True, parser)
        print '  invalidities'
        test_arguments(logic, logic.example_invalidities(), False, parser)
        

def test_arguments(logic, args, valid, parser):
    for name in args:
        print '    ', name, '...',
        arg = args[name]
        if isinstance(arg, list):
            premises = arg[0]
            conclusion = arg[1]
        else:
            premises = []
            conclusion = arg
        try:
            t = tableau(logic, parser.argument(conclusion, premises)).build()
            assert valid == t.valid
        except AssertionError as e:
            import json
            print 'FAIL'
            print t
            raise e
        print 'pass'
    
if  __name__ =='__main__':main()

def t1():
    from notations import polish
    from logics import k
    arg = polish.Parser().argument(['Cab', 'a'], 'b')
    t = tableau(k, arg)
    return t