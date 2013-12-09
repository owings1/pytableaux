from logic import *

def main():
    test()
    
def test():
    import parsers.polish
    import logics.fde, logics.cpl, logics.k, logics.t, logics.d
    logics = [
        logics.cpl, 
        logics.fde, 
        logics.k, 
        logics.t, 
        logics.d
    ]
    parser = parsers.polish.Parser()
    
    for logic in logics:
        print logic.name
        print '  validities'
        test_arguments(logic, logic.example_validities(), True, parser)
        print '  invalidities'
        test_arguments(logic, logic.example_invalidities(), False, parser)
        

def test_arguments(logic, args, valid, parser):
    for name in args:
        print '    ', name, '...',
        test_argument(logic, args[name][0], args[name][1], valid, parser)
        print 'pass'

def test_argument(logic, premises, conclusion, valid, parser):
    assert valid == tableau(logic, parser.argument(premises, conclusion)).build().valid()
    
if  __name__ =='__main__':main()

def t1():
    import parsers.polish
    import logics.k
    a = parsers.polish.Parser().argument(['Cab', 'a'], 'b')
    t = tableau(logics.k, a)
    return t