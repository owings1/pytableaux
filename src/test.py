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

import examples
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
    for logic in logics:
        print logic.name
        print '  validities'
        validity_names = sorted(logic.example_validities())
        test_arguments(logic, validity_names, True)
        print '  invalidities'
        invalidity_names = sorted(logic.example_invalidities())
        test_arguments(logic, invalidity_names, False)


def test_arguments(logic, args, valid):
    for name in args:
        print '    ', name, '...',
        arg = examples.argument(name)
        try:
            t = tableau(logic, arg).build()
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
    vocabulary = examples.vocabulary
    pol = polish.Parser(vocabulary)
    std = standard.Parser(vocabulary)
    args = examples.arguments()
    for arg in args:
        print '    ' + arg.title
        sentence_strs = [polish.write(premise) for premise in arg.premises]
        sentence_strs.append(polish.write(arg.conclusion))
        for sentence_str in sentence_strs:
            s_pol = pol.parse(sentence_str)
            s_std = std.parse(standard.write(s_pol))
            s_pol2 = pol.parse(polish.write(s_std))
            assert s_pol == s_std and s_std == s_pol2
            print '      pass: ' + polish.write(s_pol) + ' = ' + standard.write(s_std) + ' = ' + polish.write(s_pol2)
    
if  __name__ =='__main__':main()