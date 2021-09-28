# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - documentation utility functions
import examples, logic, writers.html
import codecs, inspect, os, re, traceback
from jinja2 import Environment, FileSystemLoader
from html import unescape as htmlunescape
from os.path import join as pjoin
from past.builtins import basestring
from inspect import getmro

# Alias
from logic import argument, create_parser, create_swriter, get_logic, tableau
TabSys = logic.TableauxSystem
Rule = TabSys.Rule

defaults = {
    'html_theme'       : 'default',
    'truth_tables_rev' : True,
    'write_notation'   : 'standard',
    'parse_notation'   : 'standard',
    'vocabulary'       : examples.vocabulary,
}

doc_dir = pjoin(logic.base_dir, 'doc')
templates_dir = pjoin(doc_dir, 'templates')
build_dir = pjoin(doc_dir, '_build/html')
jenv = Environment(
    loader = FileSystemLoader(templates_dir),
    trim_blocks = True,
    lstrip_blocks = True,
)
truth_table_template = jenv.get_template('truth_table.html')

# Don't build rules for abstract classes
# TODO: shouldn't this check rule groups?
skip_rules = [
    TabSys.Rule,
    TabSys.ClosureRule,
    TabSys.PotentialNodeRule,
    TabSys.FilterNodeRule,
]

skip_build_trunk = [
    TabSys.Tableau.build_trunk
]

def init_sphinx(app, opts):

    helper = Helper(opts)

    helper.connect_sphinx(app, 'autodoc-process-docstring',
        'sphinx_regex_line_replace',
        'sphinx_obj_lines_append',
    )
    helper.connect_sphinx(app, 'build-finished',
        'sphinx_docs_post_process',
    )

    app.add_css_file('css/doc.css')

    if opts['html_theme'] == 'sphinx_rtd_theme':
        themecss = 'doc.rtd.css'
    elif opts['html_theme'] == 'default':
        themecss = 'doc.default.css'
    app.add_css_file('/'.join(['css', themecss]))

    app.add_css_file('css/proof.css')

class Helper(object):

    def __init__(self, opts):
        self.opts = dict(defaults)
        self.opts.update(opts)
        self.parser = create_parser(
            notation = self.opts['parse_notation'],
            vocabulary = self.opts['vocabulary'],
        )
        self.sw = create_swriter(
            notation = self.opts['write_notation'],
            symbol_set = 'html',
        )
        self.pw = writers.html.Writer(sw = self.sw)
        # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
        self._listeners = dict()
        self._connids = dict()

    # TODO: generate rule "cheat sheet"

    ## ==============
    ##  Doc Lines   :
    ## ==============

    def lines_rule_example(self, rule, lgc=None):
        """
        Generate the rule examples.
        """
        return [
            'Example:',
            '',
            '.. raw:: html',
            '',
            cat('    ', self.html_rule_example(rule, lgc=None)),
        ]

    def lines_trunk_example(self, lgc):
        """
        Generate the build trunk examples.
        """
        return [
            'Example:',
            '',
            '.. raw:: html',
            '',
            cat('    ', self.html_trunk_example(lgc)),
        ]

    def lines_rule_docstring(self, rule, lgc=None):
        """
        Retrieve docstring lines for replacing //ruledoc//... references.
        """
        lgc = get_logic(lgc or get_obj_logic(rule))
        for name, member in inspect.getmembers(lgc.TableauxRules):
            if name == rule or member == rule:
                return [line.strip() for line in member.__doc__.split('\n')]
        raise RuleNotFoundError(
            'Rule not found: {0}, Logic: {1}'.format(str(rule), lgc.name)
        )

    def lines_logic_truth_tables(self, lgc):
        """
        Generate the truth tables for a logic.
        """
        lgc = get_logic(lgc)
        tables = [
            self.html_truth_table(lgc, operator)
            for operator in logic.operators_list
            if operator in lgc.Model.truth_functional_operators
        ]
        return [
            '.. raw:: html',
            '',
            cat('    ', *tables),
            '    <div class="clear"></div>',
            ''
        ]

    def doc_replace_lexicals(self, doc):
        """
        Replace P{A & B} notations with rendered HTML. Operates on the complete
        HTML doc at the end of the build.
        """
        is_change = False
        sw = self.sw
        for s in re.findall(r'P{(.*?)}', doc):
            s1 = htmlunescape(s)
            is_change = True
            sentence = self.parser.parse(s1)
            s2 = sw.write(sentence, drop_parens = True)
            doc = doc.replace(u'P{' + s + '}', s2)
        for s in re.findall(r'O{(.*?)}', doc):
            s1 = htmlunescape(s)
            is_change = True
            s2 = sw.write_operator(s1)
            doc = doc.replace(u'O{' + s + '}', s2)
        return (is_change, doc)

    ## =========================
    ## Sphinx Event Handlers   :
    ## =========================

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    def connect_sphinx(self, app, event, *methods):
        """
        Attach a listener to a Sphinx event. We handle our own listeners so we
        can do proper error handling. Each of `methods` can be a function or
        name of a Helper method.  One handler per event is attached to Sphinx,
        which is a lambda wrapper for ``__dispatch_sphinx()``.

        """
        if event not in self._listeners:
            self._listeners[event] = []
        for func in [
            getattr(self, method) if isinstance(method, basestring) else method
            for method in methods
        ]:
            self._listeners[event].append(func)
            print('Connecting {0} to {1}'.format(func.__name__, event))
        if event not in self._connids:
            dispatch = lambda *args: self.__dispatch_sphinx(event, args)
            self._connids[event] = app.connect(event, dispatch)
        return self

    def sphinx_regex_line_replace(self, app, what, name, obj, options, lines):
        """
        Replace a line matching a regex with 1 or more lines in a docstring.
        """
        defns = [
            (
                '//ruledoc//',
                r'//ruledoc//(.*?)//(.*)//',
                lambda lgc, rule: self.lines_rule_docstring(rule, lgc),
            ),
            (
                '//truth_tables//',
                r'//truth_tables//(.*?)//',
                self.lines_logic_truth_tables,
            ),
        ]
        i = 0
        rpl = {}
        for line in lines:
            for indic, regex, func in defns:
                if indic in line:
                    match = re.findall(regex, line)
                    if not match:
                        raise BadExpressionError(line)
                    if isinstance(match[0], basestring):
                        # Corner case of one capture group
                        match[0] = (match[0],)
                    rpl[i] = func(*match[0])
                    break
            i += 1
        for i in rpl:
            pos = i + 1
            lines[i:pos] = rpl[i]

    def sphinx_obj_lines_append(self, app, what, name, obj, options, lines):
        """
        Append lines to a docstring.
        """
        defns = [
            (
                lambda: (
                    what == 'class' and obj not in skip_rules and
                    Rule in getmro(obj)
                ),
                self.lines_rule_example,
            ),
            (
                lambda: (
                    what == 'method' and obj not in skip_build_trunk and
                    obj.__name__ == 'build_trunk'
                ),
                self.lines_trunk_example,
            )
        ]
        for check, func in defns:
            if check():
                lines += func(obj)

    def sphinx_docs_post_process(self, app, exception):
        """
        Modify the final HTML documents.
        """
        defns = [
            (self.doc_replace_lexicals,),
        ]
        print('Running post-process')
        for file in [
            pjoin(dir, file) for dir in [build_dir, pjoin(build_dir, 'logics')]
            for file in os.listdir(dir) if file.endswith('.html')
        ]:
            should_write = False
            with codecs.open(file, 'r+', 'utf-8') as f:
                doc = f.read()
                for func, in defns:
                    is_change, doc = func(doc)
                    should_write = should_write or is_change
                if should_write:
                    f.seek(0)
                    f.write(doc)
                    f.truncate()

    ## ===================
    ## HTML Subroutines  :
    ## ===================

    def html_trunk_example(self, lgc):
        """
        Returns rendered tableau HTML with argument and build_trunk example.
        """
        lgc = get_obj_logic(lgc)
        arg = argument('b', ['a1', 'a2'])
        sw = self.sw
        return cat(
            'Argument: <i>',
            '</i>, <i>'.join(sw.write(p, drop_parens=True) for p in arg.premises),
            '</i> &there4; <i>', sw.write(arg.conclusion), '</i>',
            '\n',
            self.pw.write(logic.tableau(lgc, arg).finish()),
        )

    def html_rule_example(self, rule, lgc=None):
        """
        Returns rendered tableau HTML for a rule's example application.
        """
        lgc = get_logic(lgc or get_obj_logic(rule))
        proof = tableau(lgc)
        rule = proof.get_rule(rule)
        rule.example()
        proof.branches[0].add({'ellipsis': True})
        target = rule.get_target(proof.branches[0])
        rule.apply(target)
        proof.finish()
        return self.pw.write(proof)

    def html_truth_table(self, lgc, operator):
        """
        Returns rendered truth table HTML for a single operator.
        """
        lgc = get_logic(lgc)
        table = logic.truth_table(lgc, operator, reverse = self.opts['truth_tables_rev'])
        return truth_table_template.render({
            'arity'      : logic.arity(operator),
            'sw'         : self.sw,
            'num_values' : len(lgc.Model.truth_values),
            'table'      : table,
            'operator'   : operator,
            # Theme hint for conditional class class name.
            'theme'      : self.opts['html_theme'],
        })

    ## ================
    ## Dispatcher     :
    ## ================

    def __dispatch_sphinx(self, event, args):
        for func in self._listeners[event]:
            try:
                func(*args)
            except Exception as e:
                if event == 'autodoc-process-docstring' and len(args) > 2:
                    arginfo = str({'what': args[1], 'name': args[2]})
                else:
                    arginfo = str(args)
                print('\n', '\n'.join((
                    'Failed running method {0} for event {1}'.format(
                        func.__name__, event
                    ),
                    'Exception Class: {0}, Args: {1}'.format(
                        e.__class__.__name__, str(e.args)
                    ),
                    'Event Arguments: {0}'.format(arginfo),
                )))
                print('Printing traceback')
                traceback.print_exc()
                raise e

# Misc util

def cat(*args):
    return ''.join(args)

def get_obj_logic(obj):
    try:
        return get_logic(obj)
    except:
        pass
    if hasattr(obj, '__module__'):
        # class or instance, its module is likely a logic
        return get_logic(obj.__module__)
    # Assume it's a string
    parts = obj.split('.')
    if parts[0] == 'logics':
        # logics.fde, etc.
        return get_logic('.'.join(parts[0:2]))
    # Last resort
    return get_logic(parts[0])

class BadExpressionError(Exception):
    pass

class RuleNotFoundError(Exception):
    pass