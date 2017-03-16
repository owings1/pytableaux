# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ------------------
#
# pytableaux - Test script

from logic import *
from notations import polish, standard
from logics import fde, k3, lp, go, cfol, k, d, t, s4, l3
from writers import ascii

def main():
    test_all()
    
def test_all():
    test_logics()
    test_standard_notation()
    test_notation_translations()
    
def test_logics():
    logics = [
        fde,
        k3,
        lp,
        go,
        cfol,
        k,
        d,
        t,
        s4,
        l3
    ]
    vocabulary = get_test_vocabulary()
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
            print list(t.branches)[0]
            print ascii.write(t, standard)
            raise e
        print 'pass'

def test_standard_notation():
    print "Standard notation"
    vocab = Vocabulary()
    p = standard.Parser(vocab)
    s1 = p.parse('A')
    print '      pass: ' + standard.write(s1)
    s2 = p.parse('~A')
    print '      pass: ' + standard.write(s2)
    s3 = p.parse('(A & B)')
    print '      pass: ' + standard.write(s3)
    try:
        s4 = p.parse('A & B')
        assert False, 's4 should not pass'
    except Parser.ParseError as e:
        print '      pass: ' + e.message
    try:
        s5 = p.parse('(A & B')
        assert False, 's5 should not pass'
    except Parser.ParseError as e:
        print '      pass: ' + e.message
    s6 = p.parse('((A & B) V XxXy(=xy > !a))')
    print '      pass: ' + standard.write(s6)
    s7 = p.parse('((A&B0)VXxXy(=xy>!a))')
    print '      pass: ' + standard.write(s7)
    assert s6 == s7
    print '      pass: s6 == s7'
    s8 = p.parse('(PXx!x V N=ab)')
    print '      pass: ' + standard.write(s8)

def test_notation_translations():
    print "Notation Translations"
    logics = [
        fde,
        k3,
        lp,
        go,
        cfol,
        k,
        d,
        t,
        s4,
        l3
    ]
    vocabulary = get_test_vocabulary()
    pol = polish.Parser(vocabulary)
    std = standard.Parser(vocabulary)
    example_arguments = {}
    for logic in logics:
        example_arguments.update(logic.example_validities())
        example_arguments.update(logic.example_invalidities())
    args_list = sorted(list(example_arguments.keys()))
    for arg_name in args_list:
        arg = example_arguments[arg_name]
        sentence_strs = []
        if isinstance(arg, list):
            sentence_strs += arg[0]
            sentence_strs.append(arg[1])
        else:
            sentence_strs.append(arg)
        for sentence_str in sentence_strs:
            s_pol = pol.parse(sentence_str)
            s_std = std.parse(standard.write(s_pol))
            s_pol2 = pol.parse(polish.write(s_std))
            assert s_pol == s_std and s_std == s_pol2
            print '      pass [' + arg_name + ']: ' + polish.write(s_pol) + ' = ' + standard.write(s_std) + ' = ' + polish.write(s_pol2)
    
if  __name__ =='__main__':main()