# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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
# pytableaux - documenation utility functions
import logic, writers, notations, examples
import writers.html, notations.polish, notations.standard
import inspect
import codecs
import json
import os
import re
from jinja2 import Environment, FileSystemLoader
from html.parser import HTMLParser

h = HTMLParser()

writer = writers.html.Writer()
notation = notations.standard
sp = notation.Parser(examples.vocabulary)
sw = notation.Writer('html')

doc_dir = os.path.dirname(os.path.abspath(__file__)) + '/../doc'

templates_dir = doc_dir + '/templates'

jinja_env = Environment(
    loader = FileSystemLoader(templates_dir),
    trim_blocks = True,
    lstrip_blocks = True,
)
truth_table_template = jinja_env.get_template('truth_table.html')

def get_truth_table_html(lgc, operator, table):
    s = truth_table_template.render({
        'arity'      : logic.arity(operator),
        'sentence'   : examples.operated(operator),
        'sw'         : sw,
        'values'     : lgc.Model.truth_values,
        'value_chars': lgc.Model.truth_value_chars,
        'num_values' : len(lgc.Model.truth_values),
        'table'      : table,
        'operator'   : operator,
    })
    return s

def get_truth_tables_lines_for_logic(lgc):
    lgc = logic.get_logic(lgc)
    tables = {operator: logic.truth_table(lgc, operator) for operator in lgc.Model.truth_functional_operators}
    new_lines = ['']
    for operator in logic.operators_list:
        if operator in tables:
            html = get_truth_table_html(lgc, operator, tables[operator])
            new_lines += ['    ' + line for line in html.split('\n')]
    new_lines += [
        '    <div class="clear"></div>',
        ''
    ]
    return new_lines

def get_replace_sentence_expressions_result(text, filename='unknown', is_print=False):
    found = False
    for s in re.findall(r'P{(.*?)}', text):
        s1 = h.unescape(s)
        if is_print:
            print('replacing {0} in {1}'.format(s1, filename))
        found = True
        sentence = sp.parse(s1)
        s2 = sw.write(sentence, drop_parens=True)
        text = text.replace(u'P{' + s + '}', s2)
    return {
        'is_found' : found,
        'text'     : text,
    }

class SphinxUtil(object):

    @staticmethod
    def docs_post_process(app, exception):
        # Sphinx utility
        builddir = doc_dir + '/_build/html'
        files = list()
        for f in os.listdir(builddir):
            if f.endswith('.html'):
                files.append(f)
        for f in os.listdir(builddir + '/logics'):
            if f.endswith('.html'):
                files.append('logics/' + f)
        for fil in files:
            with codecs.open(builddir + '/' + fil, 'r', 'utf-8') as f:
                text = f.read()
            result = get_replace_sentence_expressions_result(text, filename=fil, is_print=True)
            if result['is_found']:
                with codecs.open(builddir + '/' + fil, 'w', 'utf-8') as f:
                    f.write(result['text'])

    @staticmethod
    def make_truth_tables(app, what, name, obj, options, lines):
        # Sphinx utility
        srch = '/truth_tables/'
        if what == 'module' and hasattr(obj, 'Model'):
            if hasattr(obj.Model, 'truth_functional_operators') and srch in lines:
                idx = lines.index(srch)
                pos = idx + 1
                lines[idx] = '.. raw:: html'
                lines[pos:pos] = get_truth_tables_lines_for_logic(obj)

    @staticmethod
    def make_truth_tables_models(app, what, name, obj, options, lines):
        # Sphinx utility
        is_found = False
        idx = 0
        for line in lines:
            if '//truth_tables//' in line:
                is_found = True
                break
            idx += 1
        if not is_found:
            return
        pos = idx + 1
        logic_name, = re.findall(r'//truth_tables//(.*)//', lines[idx])
        lines[idx] = '.. raw:: html'
        lines[pos:pos] = get_truth_tables_lines_for_logic(logic_name)

    @staticmethod
    def make_tableau_examples(app, what, name, obj, options, lines):
        # Sphinx utility
        arg = examples.argument('Material Modus Ponens')
        if what == 'class' and logic.TableauxSystem.Rule in inspect.getmro(obj):
            mro = inspect.getmro(obj)
            if obj in [
                logic.TableauxSystem.Rule,
                logic.TableauxSystem.BranchRule,
                logic.TableauxSystem.ClosureRule,
                logic.TableauxSystem.NodeRule,
                logic.TableauxSystem.ConditionalNodeRule
            ]:
                return
            proof = None
            try:
                proof = logic.tableau(obj.__module__, None)
                rule = proof.get_rule(obj)
                rule.example()
                if len(proof.branches) == 1:
                    proof.branches[0].add({'ellipsis': True})
                target = rule.applies()
                rule.apply(target)
                proof.finish()
                lines += [
                    'Example:'                             ,
                    ''                                     ,
                    '.. raw:: html'                        ,
                    ''                                     ,
                    '    ' + writer.write(proof, sw=sw)
                ]
            except StopIteration:
                pass
            except Exception as e:
                print (str(e))
                print ('No example generated for ' + str(obj))
                if proof != None:
                    print (json.dumps(proof.tree, indent=2, default=str))
                raise e
        elif what == 'method' and obj.__name__ == 'build_trunk':
            try:
                proof = logic.tableau(obj.__module__, arg)
                proof.finish()
                lines += [
                    'Example:' ,
                    ''                                     ,
                    '.. raw:: html'                        ,
                    ''         ,
                    '    ' + 'Argument: <i>' + '</i>, <i>'.join([sw.write(p, drop_parens=True) for p in arg.premises]) + '</i> &there4; <i>' + sw.write(arg.conclusion) + '</i>',
                    ''                                     ,
                    '    ' + writer.write(proof, sw=sw)
                ]
            except Exception as e:
                print ('Error making example for ' + str(obj))
                print(str(e))
                raise e
