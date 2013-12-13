from logic import *

def main():
    test()
    
def test():
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
        try:
            t = tableau(logic, parser.argument(args[name][0], args[name][1])).build()
            assert valid == t.valid()
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