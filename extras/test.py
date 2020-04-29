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
from logics import fde, k3, k3w, b3e, lp, go, cfol, cpl, k, d, t, s4, l3
from writers import ascii

def main():
    test_all()
    
def test_all():
    test_logics()
    test_standard_notation()
    test_notation_translations()
    
def test_logics():
    logics = [
        'fde',
        'k3',
        'k3w',
        'b3e',
        'lp',
        'go',
        'cpl',
        'cfol',
        'k',
        'd',
        't',
        's4',
        'l3'
    ]
    writer = ascii.Writer()
    sw = standard.Writer()
    for name in examples.args_list:
        arg = examples.argument(name)
        print(name)
        for logic_name in logics:
            logic = get_logic(logic_name)
            if name in logic.example_validities():
                expect = True
            elif name in logic.example_invalidities():
                expect = False
            else:
                expect = None
            print '    {0: <6} : '.format(logic.name),
            try:
                t = tableau(logic, arg).build()
            except:
                print("Failed to evaluate '{0}' in {1}".format(name, logic.name))
                raise
            result_str = 'VALID' if t.valid else 'INVALID'
            if expect != None:
                pass_str = 'PASS' if expect == t.valid else 'FAIL'
                ok = expect == t.valid
            else:
                pass_str = 'UNKNOWN'
                ok = True
            print('{0: <8} : {1}'.format(result_str, pass_str))
            if not ok:
                print t
                print list(t.branches)[0]
                print writer.write(t, writer=sw)
                raise Exception("Expectation failed for '{0}' in {1}".format(name, logic.name))

def test_standard_notation():
    print "Standard notation"
    vocab = Vocabulary()
    p = standard.Parser(vocab)
    w = standard.Writer()
    s1 = p.parse('A')
    print '      pass: ' + w.write(s1)
    s2 = p.parse('~A')
    print '      pass: ' + w.write(s2)
    s3 = p.parse('(A & B)')
    print '      pass: ' + w.write(s3)
    s4 = p.parse('A & B')
    print '      pass: ' + w.write(s3)
    try:
        s5 = p.parse('(A & B')
        assert False, 's5 should not pass'
    except Parser.ParseError as e:
        print '      pass: ' + e.message
    s6 = p.parse('((A & B) V XxXy(=xy > !a))')
    print '      pass: ' + w.write(s6)
    s7 = p.parse('((A&B0)VXxXy(=xy>!a))')
    print '      pass: ' + w.write(s7)
    assert s6 == s7
    print '      pass: s6 == s7'
    s8 = p.parse('(PXx!x V N=ab)')
    print '      pass: ' + w.write(s8)

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
    ws = standard.Writer()
    wp = polish.Writer()
    args = examples.arguments()
    for arg in args:
        print '    ' + arg.title
        sentence_strs = [wp.write(premise) for premise in arg.premises]
        sentence_strs.append(wp.write(arg.conclusion))
        for sentence_str in sentence_strs:
            s_pol = pol.parse(sentence_str)
            s_std = std.parse(ws.write(s_pol))
            s_pol2 = pol.parse(wp.write(s_std))
            assert s_pol == s_std and s_std == s_pol2
            print '      pass: ' + wp.write(s_pol) + ' = ' + ws.write(s_std) + ' = ' + wp.write(s_pol2)
    
if  __name__ =='__main__':main()