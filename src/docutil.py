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

import codecs, inspect, os, re, traceback
from jinja2 import Environment, FileSystemLoader
from html import escape as htmlesc, unescape as htmlun
from os.path import join as pjoin, basename as bname
from past.builtins import basestring
from inspect import getmro, getsource, isclass, ismethod

from sphinx.util import logging
from docutils import nodes
from docutils.parsers.rst import Directive, directives, roles

logger = logging.getLogger(__name__)
from utils import cat, get_logic
import examples
from lexicals import Argument, operarity, create_lexwriter
from parsers import create_parser, parse_argument
from tableaux import Tableau, TableauxSystem as TabSys, Rule, ClosureRule, \
    PotentialNodeRule, FilterNodeRule, create_tabwriter
from models import truth_table
from fixed import base_dir, operators_list

defaults = {
    'html_theme'       : 'default',
    'truth_tables_rev' : True,
    'write_notation'   : 'standard',
    'parse_notation'   : 'standard',
    'vocabulary'       : examples.vocabulary,
}

# Python domain:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html?#the-python-domain
# Autodoc directives:
#    https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directives
# Built-in roles:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html
# Sphinx events:
#    https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

doc_dir = pjoin(base_dir, 'doc')
templates_dir = pjoin(doc_dir, 'templates')
build_dir = pjoin(doc_dir, '_build/html')
jenv = Environment(
    loader = FileSystemLoader(templates_dir),
    trim_blocks = True,
    lstrip_blocks = True,
)
truth_table_template = jenv.get_template('truth_table.html')

lgclist = [
    bname('.'.join(file.split('.')[0:-1])).upper() for file in
    os.listdir(pjoin(doc_dir, 'logics'))
    if file.endswith('.rst')
]

def init_sphinx(app, opts):

    helper = Helper(opts)

    # helper.connect_sphinx(app, 'autodoc-process-signature',
    #     'sphinx_filter_signature',
    # )
    helper.connect_sphinx(app, 'autodoc-process-docstring',
        'sphinx_obj_lines_append_autodoc',
        'sphinx_regex_line_replace_autodoc',
        'sphinx_regex_simple_replace_autodoc',
    )

    helper.connect_sphinx(app, 'source-read',
        'sphinx_regex_line_replace_source',
        'sphinx_regex_simple_replace_source',
    )

    helper.connect_sphinx(app, 'build-finished',

    )

    app.add_role('s', helper.role_lexrender_auto)
    app.add_role('oper', helper.role_lexrender_oper)
    app.add_role('m', helper.role_lexrender_meta)

    app.add_css_file('css/doc.css')

    if opts['html_theme'] == 'sphinx_rtd_theme':
        themecss = 'doc.rtd.css'
    elif opts['html_theme'] == 'default':
        themecss = 'doc.default.css'
    app.add_css_file('/'.join(['css', themecss]))

    app.add_css_file('css/proof.css')

def sphinx_role_defaults(func):
    func.options = {'class': directives.class_option}
    func.content = True
    return func

class Helper(object):

    def __init__(self, opts={}):
        self.opts = dict(defaults)
        self.opts.update(opts)
        # print('\n\n', str(self.opts))
        self.parser = create_parser(
            notn = self.opts['parse_notation'],
            vocab = self.opts['vocabulary'],
        )
        # print('\n\n', self.parser.__class__.__name__)
        self.lw = create_lexwriter(
            notn = self.opts['write_notation'],
            format = 'html',
        )
        self.pw = create_tabwriter(
            notn = self.opts['write_notation'],
            format = 'html',
        )
        self.replace_defns = []
        # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
        self._listeners = dict()
        self._connids = dict()

    # TODO: generate rule "cheat sheet"

    ## ==============
    ##  Doc Lines   :
    ## ==============

    def lines_rule_example(self, rule, lgc=None, indent=None):
        """
        Generate the rule examples. Lines are returned properly indented
        if indent is specified.
        """
        plines = self.html_rule_example(rule, lgc=None).split('\n')
        return indent_lines(['Example:', '', *rawblock(plines)], indent = indent)

    def lines_trunk_example(self, lgc, indent=None):
        """
        Generate the build trunk examples. Lines are returned properly indented
        if indent is specified.
        """
        plines = self.html_trunk_example(lgc).split('\n')
        return indent_lines(['Example:', '', *rawblock(plines)], indent = indent)

    def lines_logic_truth_tables(self, lgc, indent=None):
        """
        Generate the truth tables for a logic. Lines are returned properly
        indented if indent is specified.
        """
        lgc = get_logic(lgc)
        tables = [
            self.html_truth_table(lgc, operator)
            for operator in operators_list
            if operator in lgc.Model.truth_functional_operators
        ]
        lines = '\n'.join(tables).split('\n')
        lines.append('<div class="clear"></div>')
        return rawblock(lines, indent = indent)

    def lines_rule_docstring(self, rule, lgc=None, indent=None):
        """
        Retrieve docstring lines for replacing //ruledoc//... references.
        Lines are returned properly indented if indent is specified.
        """
        lgc = get_logic(lgc or get_obj_logic(rule))
        found = None
        for name, member in inspect.getmembers(lgc.TableauxRules):
            if name == rule or member == rule:
                found = member
                break
        if not found:
            raise RuleNotFoundError(
                'Rule not found: {0}, Logic: {1}'.format(str(rule), lgc.name)
            )
        lines = [line.strip() for line in found.__doc__.split('\n')]
        return indent_lines(lines, indent = indent)

    def lines_inherited_ruledoc(self, rule, indent=None):
        """
        Generate entire doc block for an inherited rule.
        """
        prule = getmro(rule)[1]
        plgc = get_obj_logic(prule)
        lines = [
            '*This rule is the same as* :class:`{0} {1}'.format(plgc.name, prule.__name__),
            '<{0}.{1}>`'.format(prule.__module__, prule.__qualname__),
            '',
            *self.lines_rule_docstring(prule, lgc=plgc),
            '',
        ]
        return indent_lines(lines, indent = indent)

    def lines_opers_table(self, indent=None):
        sympol, symstd, symhtml = (
            symset.chars('operator') for symset in (
                create_parser('polish',  format='ascii').symbol_set,
                create_parser('standard', format='ascii').symbol_set,
                create_lexwriter('standard', format='html').symbol_set,
            )
        )
        lines = [
            '"Operator Name","Arity","Polish","Standard","HTML"'
        ] + [
            '"{0}","{1}","``{2}``","``{3}``","{4}"'.format(*row)
            for row in (
                (o, str(operarity(o)), sympol[o], symstd[o], htmlun(symhtml[o]))
                for o in operators_list
            )
        ]
        return indent_lines(lines, indent = indent)

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
            logger.info('Connecting {0} to {1}'.format(func.__name__, event))
        if event not in self._connids:
            dispatch = lambda *args: self.__dispatch_sphinx(event, args)
            self._connids[event] = app.connect(event, dispatch)
        return self

    def sphinx_regex_simple_replace_common(self, lines, is_source=False):
        logicmatch = '|'.join(v.upper() for v in lgclist)
        defns = [
            # Truth values
            (r'{v.([TBNF])}', ':math:`\\1`'),
            # Logic class links like {@FDE}
            (
                r'{{@({0})}}'.format(logicmatch),
                lambda pat: (
                    ':class:`{0} <logics.{1}>`'.format(
                        pat.group(1), pat.group(1).lower()
                    )
                )
            ),
            # Meta-tuple params - {@metuple}
            ('{@metuple}', ':math:`\\\\langle a_0,...,a_n\\\\rangle`'),
        ]
        text = '\n'.join(lines)
        for regex, repl in defns:
            text = re.sub(regex, repl, text)
        if is_source:
            lines[0]= text
        else:
            lines.clear()
            lines.extend(text.split('\n'))

    def sphinx_regex_simple_replace_source(self, app, docname, lines):
        self.sphinx_regex_simple_replace_common(lines, is_source = True)

    def sphinx_regex_simple_replace_autodoc(self, app, what, name, obj, options, lines):
        self.sphinx_regex_simple_replace_common(lines, is_source = False)

    def sphinx_regex_line_replace_common(self, lines, is_source=False):
        """
        Replace a line matching a regex with 1 or more lines. Lines could come
        from autodoc extraction or straight from source. In the latter case,
        it is important to observe correct indenting for new lines.

        This matches the first occurrence in a line and replaces that line with
        the line(s) returned. So these kinds of matches should generally be
        the only thing on a line.
        """
        defns = [
            (
                '//ruledoc//',
                r'(\s*)//ruledoc//(.*?)//(.*)//',
                lambda indent, lgc, rule: (
                    self.lines_rule_docstring(rule, lgc = lgc, indent = indent)
                ),
            ),
            (
                '//truth_tables//',
                r'(\s*)//truth_tables//(.*?)//',
                lambda indent, lgc: (
                    self.lines_logic_truth_tables(lgc, indent = indent)
                ),
            ),
            (
                '//lexsym_opers_csv//',
                r'(\s*)//lexsym_opers_csv//',
                self.lines_opers_table,
            )
        ]
        proclines = lines[0].split('\n') if is_source else lines
        i = 0
        rpl = {}
        for line in proclines:
            for indic, regex, func in defns:
                #print(lines)
                if indic in line:
                    matches = re.findall(regex, line)
                    if not matches:
                        raise BadExpressionError(line)
                    match = matches[0]
                    if isinstance(match, basestring):
                        # Corner case of one capture group
                        match = (match,)
                    rpl[i] = func(*match)
                    break
            i += 1
        for i in rpl:
            pos = i + 1
            proclines[i:pos] = rpl[i]
        if rpl and is_source:
            lines[0] ='\n'.join(proclines)

    def sphinx_regex_line_replace_source(self, app, docname, lines):
        """
        Replace a line matching a regex with 1 or more lines in a docstring.
        """
        self.sphinx_regex_line_replace_common(lines, is_source = True)

    def sphinx_regex_line_replace_autodoc(self, app, what, name, obj, options, lines):
        """
        Regex line replace for autodoc event. Delegate to common method.
        """
        self.sphinx_regex_line_replace_common(lines, is_source = False)

    # Don't build rules for abstract classes
    # TODO: shouldn't this check rule groups?
    skip_rules = [
        Rule,
        ClosureRule,
        PotentialNodeRule,
        FilterNodeRule,
    ]

    skip_trunks = [
        Tableau.build_trunk
    ]

    def sphinx_obj_lines_append_autodoc(self, app, what, name, obj, options, lines):
        """
        Append lines to a docstring extracted from the autodoc extention. For injecting
        into doc source files, use a regex line replacement.
        """
        defns = [
            (
                self.should_inherit_ruledoc,
                self.lines_inherited_ruledoc,
            ),
            (
                Rule in safemro(obj) and obj not in self.skip_rules,
                self.lines_rule_example,
            ),
            (
                TabSys.build_trunk in methmro(obj) and obj not in self.skip_trunks,
                self.lines_trunk_example,
            )
        ]
        for check, func in defns:
            if check and (not callable(check) or check(obj)):
                lines += func(obj)

    ## ===================
    ## HTML Subroutines  :
    ## ===================

    def html_trunk_example(self, lgc):
        """
        Returns rendered tableau HTML with argument and build_trunk example.
        """
        lgc = get_obj_logic(lgc)
        arg = parse_argument('b', ['a1', 'a2'], notn='polish')
        lw = self.lw
        return cat(
            'Argument: <i>',
            '</i>, <i>'.join(lw.write(p) for p in arg.premises),
            '</i> &there4; <i>', lw.write(arg.conclusion), '</i>',
            '\n',
            self.pw.write(Tableau(lgc, arg).finish()),
        )

    def html_rule_example(self, rule, lgc=None):
        """
        Returns rendered tableau HTML for a rule's example application.
        """
        lgc = get_logic(lgc or get_obj_logic(rule))
        proof = Tableau(lgc)
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
        table = truth_table(lgc, operator, reverse = self.opts['truth_tables_rev'])
        return truth_table_template.render({
            'arity'      : operarity(operator),
            'num_values' : len(lgc.Model.truth_values),
            'table'      : table,
            'operator'   : operator,
            'lw'         : self.lw,
            # Theme hint for conditional class class name.
            'theme'      : self.opts['html_theme'],
        })

    ## ================
    ## Custom Roles   :
    ## ================

    def lexrender_common(self, text, opts, what=None):
        """
        From: https://docutils.sourceforge.io/docs/howto/rst-roles.html

        Role functions return a tuple of two values:

        * A list of nodes which will be inserted into the document tree at the
        point where the interpreted role was encountered (can be an empty
        list).

        * A list of system messages, which will be inserted into the document tree
        immediately after the end of the current block (can also be empty).
        """
        lw = self.lw
        parse = self.parser.parse
        if text.startswith('oper.'):
            what = 'operator'
            text = text.split('.')[1]
        # elif text.startswith('pred.'):
        #     what = 'pred'
        #     text = text.split('.')[1]
        elif not what:
            what = 'sentence'
        if what == 'sentence':
            raw = lw.write(parse(text))
        elif what == 'operator':
            raw = lw.write_operator(text)
        else:
            raise UnknownLexTypeError('Unknown lexical type: {0}'.format(what))
        rendered = htmlun(raw)
        node = nodes.inline(text = rendered)
        set_classes(opts)
        return ([node], [])

    @sphinx_role_defaults
    def role_lexrender_auto(self, name, rawtext, text, lineno, inliner, opts={}, content=[]):
        return self.lexrender_common(text, opts)

    @sphinx_role_defaults
    def role_lexrender_oper(self, name, rawtext, text, lineno, inliner, opts={}, content=[]):
        return self.lexrender_common(text, opts, what = 'operator')

    @sphinx_role_defaults
    def role_lexrender_meta(self, name, rawtext, text, lineno, inliner, opts={}, content=[]):
        
        ismath = True
        bs = '\\'
        if text == 'ntuple':
            # ntuple
            rend = cat(bs, 'langle a_0,...,a_n', bs, 'rangle')
            #rend = ':math:`\\\\langle a_0,...,a_n\\\\rangle`'
        elif text in ('T', 'F', 'N', 'B'):
            rend = text
        else:
            if '.' in text:
                pfx, text = text.split('.', 1)
            else:
                raise UnknownLexTypeError('Unspecified metalexical type: {0}'.format(text))
            if pfx == 'v':
                # truth-values
                # escape for safety
                rend = htmlesc(text)
            else:
                raise UnknownLexTypeError('Unknown metalexical type: {0}'.format(pfx))
        if ismath:
            node = nodes.math(text = rend)
        else:
            node = nodes.inline(text = rend)
        set_classes(opts)
        return ([node], [])

    ## ================
    ## Dispatcher     :
    ## ================

    def __dispatch_sphinx(self, event, args):
        for func in self._listeners[event]:
            try:
                func(*args)
            except Exception as e:
                extra = ''
                if event == 'autodoc-process-docstring' and len(args) > 2:
                    arginfo = str({'what': args[1], 'name': args[2]})
                elif event == 'source-read' and len(args) > 2:
                    arginfo = '\n'.join((
                        '',
                        'docname: {0}\n'.format(args[1]),
                        'content: \n\n{0}'.format('\n'.join(args[2])),
                    ))
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

    ## Other
    def should_inherit_ruledoc(self, rule):
        """
        if a rule:
            - is included in TableauRules groups for the module it belongs to
            - inherits from a rule class that belongs to another logic module
            - the parent class is in the other logic's rule goups
            - there is no implementation besides pass
            - there is no dockblock
        then:
            - add a template message like *This rule is the same as* :class:...
            - append the parent rule's dock
            - add a hidden indicator in that it was generated
        """
        # print('Checking:', str(rule))
        check = (
            isnodoc(rule) and isnocode(rule) and
            selfgrouped(rule) and parentgrouped(rule)
        )
        if check:
            # print('INHERIT', str(rule))
            return True
        return False

# Misc util

def rawblock(lines, indent=None):
    """
    Make a raw html block from the lines. Returns a new list of lines.
    """
    return indent_lines(
        ['.. raw:: html', '', *indent_lines(lines, 4), ''],
        indent = indent,
    )

def indent_lines(lines, indent=None):
    """
    Indent non-empty lines. Indent can be string or number of spaces.
    """
    if not indent:
        indent = ''
    elif isinstance(indent, int):
        indent *= ' '
    return [cat(indent, line) if len(line) else line for line in lines]

def safemro(obj):
    """Try to get the mro of the class, else empty list"""
    try:
        return getmro(obj)
    except:
        return []

def methmro(meth):
    """Get the methods of the same name of the mro (safe) of the class the method is bound to"""
    try:
        clsmro = getmro(meth.__self__)
        meths = [getattr(c, meth.__name__, None) for c in clsmro]
        return [m for m in meths if m]
    except:
        return []

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

def isnodoc(obj):
    return not bool(getattr(obj, '__doc__', False))

def isnocode(obj):
    try:
        lines = [
            line for line in [line.strip() for line in getsource(obj).split('\n')] if line
        ]
        isblock = False
        isfirst = True
        for line in lines:
            # print('line:'+line)
            if isfirst:
                isfirst = False
                regex = r'^(class|def) {0}(\([a-zA-Z0-9_.]+\))?:$'.format(obj.__name__)
                # print('regex: ', regex)
                m = re.findall(regex, line)
                # print('m: ', str(m))
                if not m:
                    # print('oh nod')
                    return False
                continue
            if line.startswith('#'):
                continue
            if line == 'pass':
                continue
            if line.startswith('"""'):
                # not perfect, but more likely to produce false negatives
                # than false positives
                isblock = not isblock
                continue
            if isblock:
                continue
            # print('uh on')
            return False
        return True
    except:
        # raise
        return False

def rulegrouped(rule, lgc):
    if Rule not in safemro(rule):
        return False
    try:
        lgc = get_logic(lgc)
        rcls = lgc.TableauxRules
        if rule in rcls.closure_rules:
            return True
        for grp in rcls.rule_groups:
            if rule in grp:
                return True
        return False
    except:
        return False

def selfgrouped(rule):
    try:
        return rulegrouped(rule, get_obj_logic(rule))
    except:
        return False

def parentgrouped(rule):
    try:
        parent = getmro(rule)[1]
        plgc = get_obj_logic(parent)
        return rulegrouped(parent, plgc)
    except:
        return False

def set_classes(options):
    """
    From: https://github.com/docutils-mirror/docutils/blob/master/docutils/parsers/rst/roles.py#L385

    Auxiliary function to set options['classes'] and delete
    options['class'].
    """
    if 'class' in options:
        assert 'classes' not in options
        options['classes'] = options['class']
        del options['class']

class BadExpressionError(Exception):
    pass

class RuleNotFoundError(Exception):
    pass

class UnknownLexTypeError(Exception):
    pass



# class ParseRenderDirective(Directive):
#     sp = create_parser(
#         notation = 'standard',
#         vocabulary = examples.vocabulary,
#     )
#     sw = create_swriter(
#         notation = 'standard',
#         symbol_set = 'html',
#     )
#     has_content = True
#     required_arguments = 0
#     optional_arguments = 2
#     final_argument_whitespace = False
#     def run(self):
#         print('\n'.join((
#             '\ncontent:\n', str(self.content),
#         )))
#         node = nodes.inline(text=self.sw.write(self.sp.parse('A V ~A')))
#         return [node]
# def sphinx_filter_signature(self, app, what, name, obj, options, signature, return_annotation):
#     raise NotImplementedError()
#     if what == 'class' and name.startswith('logics.') and '.TableauxRules.' in name:
#         # check if it is in use in rule groups
#         lgc = get_obj_logic(obj)
#         isfound = False
#         if obj in lgc.TableauxRules.closure_rules:
#             print('CLUSRE', name, lgc.name)
#             isfound = True
#         if not isfound:
#             for grp in lgc.TableauxRules.rule_groups:
#                 if obj in grp:
#                     print('Found', name, lgc.name)
#                     isfound = True
#                     break
#         if not isfound:
#             print('NOTFOUND', name, lgc.name)
#             return
        
#         if signature=='(*args, **opts)':
#             ret = ('()', return_annotation)
#             ret = ('', return_annotation)
#             print((signature, return_annotation), '=>', ret)
#             return '(*args)', return_annotation
#             return ret
#             #eturn ('()', return_annotation)
#     return signature

# def sphinx_docs_post_process(self, app, exception):
#     """
#     Post process
#     """
#     raise NotImplementedError()
#     defns = [
#         # (self.doc_replace_lexicals,),
#     ]
#     if not defns:
#         return
#     if exception:
#         print('Not running post process due to exception')
#         return
#     print('Running post-process')
#     for file in [
#         pjoin(dir, file) for dir in [build_dir, pjoin(build_dir, 'logics')]
#         for file in os.listdir(dir) if file.endswith('.html')
#     ]:
#         should_write = False
#         with codecs.open(file, 'r+', 'utf-8') as f:
#             doc = f.read()
#             for func, in defns:
#                 is_change, doc = func(doc)
#                 should_write = should_write or is_change
#             if should_write:
#                 f.seek(0)
#                 f.write(doc)
#                 f.truncate()