from logic import *

def main():
    test_all()
    
def test_all():
    test_logics()
    
def test_logics():
    from notations import polish
    from logics import fde, cpl, k, d, t, s4
    logics = [
        fde,
        cpl,
        k,
        d,
        t,
        s4
    ]
    parser = polish.Parser()
    
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