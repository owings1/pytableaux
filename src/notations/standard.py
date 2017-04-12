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
# pytableaux - Standard Notation

import logic, string

name = 'Standard'

symbol_sets = {
    'default' : logic.Parser.SymbolSet('default', {
        'atomic' : ['A', 'B', 'C', 'D', 'E'],
        'operator' : {
            'Assertion'              :  '*',
            'Negation'               :  '~',
            'Conjunction'            :  '&',
            'Disjunction'            :  'V',
            'Material Conditional'   :  '>',
            'Material Biconditional' :  '<',
            'Conditional'            :  '$',
            'Biconditional'          :  '%',
            'Possibility'            :  'P',
            'Necessity'              :  'N',
        },
        'variable' : ['x', 'y', 'z', 'v'],
        'constant' : ['a', 'b', 'c', 'd'],
        'quantifier' : {
            'Universal'   : 'L',
            'Existential' : 'X',
        },
        'system_predicate'  : {
            'Identity'  : '=',
            'Existence' : '!',
        },
        'user_predicate'  : ['F', 'G', 'H', 'O'],
        'paren_open'      : ['('],
        'paren_close'     : [')'],
        'whitespace'      : [' '],
        'digit'           : list(string.digits)
    }),
    # see http://www.webstandards.org/learn/reference/charts/entities/symbol_entities/
    # and https://www.johndcook.com/blog/math_symbols/
    # and https://www.w3schools.com/charsets/ref_utf_geometric.asp
    'html'    : logic.Parser.SymbolSet('html', {
        'atomic'   : ['A', 'B', 'C', 'D', 'E'],
        'operator' : {
            'Assertion'              : '&deg;'   ,
            'Negation'               : '&not;'   ,
            'Conjunction'            : '&and;'   ,
            'Disjunction'            : '&or;'    ,
            'Material Conditional'   : '&sup;'   ,
            'Material Biconditional' : '&equiv;' ,
            'Conditional'            : '&rarr;'  ,
            'Biconditional'          : '&harr;'  ,
            'Possibility'            : '&#9671;' ,
            'Necessity'              : '&#9723;' ,
        },
        'variable'   : ['x', 'y', 'z', 'v'],
        'constant'   : ['a', 'b', 'c', 'd'],
        'quantifier' : {
            'Universal'   : '&forall;' ,
            'Existential' : '&exist;'  ,
        },
        'system_predicate'  : {
            'Identity'  : '=',
            'Existence' : '!',
            'NegatedIdentity' : '&ne;',
        },
        'user_predicate'  : ['F', 'G', 'H', 'O'],
        'paren_open'      : ['('],
        'paren_close'     : [')'],
        'whitespace'      : [' '],
        'digit'           : list(string.digits)
    })
}

class Writer(logic.Vocabulary.Writer):

    symbol_sets = symbol_sets

    def write(self, sentence, symbol_set = None, **opts):
        if sentence.is_operated() and 'drop_parens' in opts and opts['drop_parens']:
            return self.write_operated(sentence, symbol_set = symbol_set, drop_parens = True)
        else:
            return super(Writer, self).write(sentence, symbol_set = symbol_set, **opts)

    def write_predicated(self, sentence, symbol_set = None):
        symset = self.symset(symbol_set)
        if sentence.predicate.arity < 2:
            return super(Writer, self).write_predicated(sentence, symbol_set = symbol_set)
        joins = [self.write_parameter(sentence.parameters[0], symbol_set = symbol_set)]
        if sentence.predicate.name == 'Identity':
            joins.append(symset.charof('whitespace', 0))
        joins.append(self.write_predicate(sentence.predicate, symbol_set = symbol_set))
        if sentence.predicate.name == 'Identity':
            joins.append(symset.charof('whitespace', 0))
        joins += [self.write_parameter(param, symbol_set = symbol_set) for param in sentence.parameters[1:]]
        return ''.join(joins)

    def write_operated(self, sentence, symbol_set = None, drop_parens = False):
        symset = self.symset(symbol_set)
        arity = logic.arity(sentence.operator)
        if arity == 1:
            if (symset.name == 'html' and
                sentence.operator == 'Negation' and
                sentence.operand.is_predicated() and
                sentence.operand.predicate.name == 'Identity'):
                return self.write_html_negated_identity(sentence, symbol_set = symbol_set)
            else:
                return symset.charof('operator', sentence.operator) + self.write(sentence.operand, symbol_set = symbol_set)
        elif arity == 2:
            return ''.join([
                symset.charof('paren_open', 0) if not drop_parens else '',
                symset.charof('whitespace', 0).join([
                    self.write(sentence.lhs, symbol_set = symbol_set),
                    symset.charof('operator', sentence.operator),
                    self.write(sentence.rhs, symbol_set = symbol_set)
                ]),
                symset.charof('paren_close', 0) if not drop_parens else ''
            ])
        else:
            raise Exception(NotImplemented)

    def write_html_negated_identity(self, sentence, symbol_set = None):
        symset = self.symset(symbol_set)
        params = sentence.operand.parameters
        joins = [
            self.write_parameter(params[0], symbol_set = symbol_set),
            symset.charof('whitespace', 0),
            symset.charof('system_predicate', 'NegatedIdentity'),
            symset.charof('whitespace', 0),
            self.write_parameter(params[1], symbol_set = symbol_set)
        ]
        return ''.join(joins)
            
class Parser(logic.Parser):

    symbol_sets = {'default': symbol_sets['default']}

    def parse(self, string):
        try:
            s = super(Parser, self).parse(string)
        except logic.Parser.ParseError as e:
            try:
                # allow dropped outer parens
                pstring = ''.join([
                    self.symbol_set.charof('paren_open', 0),
                    string,
                    self.symbol_set.charof('paren_close', 0)
                ])
                s = super(Parser, self).parse(pstring)
            except logic.Parser.ParseError as e1:
                raise e
            else:
                return s
        else:
            return s

    def read(self):
        ctype = self.assert_current()
        if ctype == 'operator':
            s = self.read_operator_sentence()
        elif ctype == 'paren_open':
            s = self.read_from_open_paren()
        elif ctype == 'variable' or ctype == 'constant':
            s = self.read_infix_predicate_sentence()
        else:
            s = super(Parser, self).read()
        return s

    def read_operator_sentence(self):
        operator = self.symbol_set.indexof('operator', self.current())
        arity = logic.arity(operator)
        # only unary operators can be prefix operators
        if arity != 1:
            raise logic.Parser.ParseError("Unexpected non-prefix operator symbol '{0}' at position {1}.".format(self.current(), self.pos))
        self.advance()
        operand = self.read()
        return logic.operate(operator, [operand])

    def read_infix_predicate_sentence(self):
        params = [self.read_parameter()]
        self.assert_current_is('user_predicate', 'system_predicate')
        ppos = self.pos
        predicate = self.read_predicate()
        if predicate.arity < 2:
            raise logic.Parser.ParseError("Unexpected {0}-ary predicate at position {1}. Infix notation requires arity > 1.".format(predicate.arity, ppos))
        params += self.read_parameters(predicate.arity - 1)
        return logic.predicated(predicate, params)

    def read_from_open_paren(self):
        # if we have an open parenthesis, then we demand a binary infix operator sentence.
        # scan ahead to:
        #   - find the corresponding close parenthesis position
        #   - find the binary operator and its position
        operator = None
        operator_pos = None
        depth = 1
        length = 1
        while depth:
            if not self.has_next(length):
                raise logic.Parser.ParseError('Unterminated open parenthesis at position {0}.'.format(self.pos))
            peek = self.next(length)
            ptype = self.typeof(peek)
            if ptype == 'paren_close':
                depth -= 1
            elif ptype == 'paren_open':
                depth += 1
            elif ptype == 'operator':
                peek_operator = self.symbol_set.indexof('operator', peek)
                if logic.arity(peek_operator) == 2 and depth == 1:
                    if operator != None:
                        raise logic.Parser.ParseError('Unexpected binary operator at position {0}.'.format(self.pos + length))
                    operator_pos = self.pos + length
                    operator = peek_operator
            length += 1
        if length == 1:
            raise logic.Parser.ParseError('Empty parenthetical expression at position {0}.'.format(self.pos))
        if operator == None:
            raise logic.Parser.ParseError('Parenthetical expression is missing binary operator at position {0}.'.format(self.pos))
        # now we can divide the string into lhs and rhs
        lhs_start = self.pos + 1
        # move past the open paren
        self.advance()
        # read the lhs
        lhs = self.read()
        self.chomp()
        if self.pos != operator_pos:
            raise logic.Parser.ParseError(
                ''.join([
                    'Invalid left side expression starting at position {0} and ending at position {1},',
                    'which proceeds past operator ({2}) at position {3}.'
                ]).format(
                    lhs_start, self.pos, operator, operator_pos
                )
            )
        # move past the operator
        self.advance()
        # read the rhs
        rhs = self.read()
        self.chomp()
        # now we should have a close paren
        self.assert_current_is('paren_close')
        # move past the close paren
        self.advance()
        return logic.operate(operator, [lhs, rhs])

writer = Writer()
def write(sentence, symbol_set = None):
    return writer.write(sentence, symbol_set = symbol_set, drop_parens = True)