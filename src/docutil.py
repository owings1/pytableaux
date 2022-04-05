# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
from __future__ import annotations
from collections import defaultdict

import inspect, os, re, traceback
from typing import Any, Callable
from jinja2 import Environment, FileSystemLoader
from html import escape as htmlesc, unescape as htmlun
from os.path import abspath, join as pjoin, basename as bname
from inspect import getmro, getsource #, isclass, ismethod
from copy import deepcopy

from sphinx.application import Sphinx
from sphinx.util import logging
import docutils, docutils.nodes as docnodes, docutils.nodes as nodes

# from docutils.parsers.rst import Directive, roles
import docutils.parsers.rst.directives as directives
from tools.abcs import F, MapProxy

from tools.misc import cat, get_logic
import examples
from lexicals import (
    BaseLexWriter,
    Constant,
    Notation,
    Variable,
    RenderSet,
    Predicate,
    Predicates,
    Operator,
    LexType,
    LexWriter,
)
from parsers import create_parser, parse_argument, ParseTable
from proof.tableaux import (
    Tableau,
    TableauxSystem as TabSys,
    Rule,
    ClosingRule,
)
from proof.writers import TabWriter
from proof.helpers import EllipsisExampleHelper
from models import BaseModel

# Python domain:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html?#the-python-domain
# Autodoc directives:
#    https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directives
# Built-in roles:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html
# Sphinx events:
#    https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
# Docutils doctree:
#    https://docutils.sourceforge.io/docs/ref/doctree.html
# Font (GPL):
#    http://www.gust.org.pl/projects/e-foundry/tg-math/download/index_html#Bonum_Math

DOC_DIR = abspath(pjoin(os.path.dirname(__file__), '../doc'))
TEMPLATES_DIR = pjoin(DOC_DIR, 'templates')
JENV = Environment(
    loader = FileSystemLoader(TEMPLATES_DIR),
    trim_blocks = True,
    lstrip_blocks = True,
)
LOGICS = tuple(
    bname('.'.join(file.split('.')[0:-1])).upper()
    for file in os.listdir(pjoin(DOC_DIR, 'logics'))
    if file.endswith('.rst')
)


logger = logging.getLogger(__name__)




class Helper:

    @staticmethod
    def setup_sphinx(app: Sphinx, opts: dict) -> Helper:

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

        # helper.connect_sphinx(app, 'build-finished',

        # )

        # helper.connect_sphinx(app, 'object-description-transform',
        #     'sphinx_evtest',
        # )
        app.add_role('s', helper.role_lexrender_auto)
        app.add_role('oper', helper.role_lexrender_oper)
        app.add_role('m', helper.role_lexrender_meta)

        return helper

    # Don't build rules for abstract classes
    # TODO: shouldn't this check rule groups?
    SKIP_RULES = Rule, ClosingRule

    SKIP_TRUNKS = (
        TabSys.build_trunk,
        # Tableau.build_trunk
    )

    TT_TEMPL = JENV.get_template('truth_table.jinja2')

    _defaults = MapProxy(dict(
        truth_tables_rev = True,
        write_notation   = Notation.standard,
        parse_notation   = Notation.standard,
        preds            = examples.preds,
    ))

    def __init__(self, opts: dict = {}):

        self.opts = dict(self._defaults) | opts

        self.parser = create_parser(
            notn = self.opts['parse_notation'],
            vocab = self.opts['preds'],
        )

        wrnotn = self.opts['write_notation']

        self.lw: BaseLexWriter = LexWriter(wrnotn, charset = 'html')
        self.pwrule = TabWriter('html',
            lw = self.lw,
            classes = ['example', 'rule'],
        )
        self.pwclosure = TabWriter('html',
            lw = self.lw,
            classes = ['example', 'rule', 'closure'],
        )

        rsdata = deepcopy(self.lw.renderset.data)
        if 'renders' not in rsdata:
            rsdata['renders'] = {}
        rsdata['renders']['subscript'] = lambda sub: (
            '<sub>{0}</sub>'.format('n' if sub == 2 else sub)
        )
        rset = RenderSet(rsdata)

        self.lwtrunk = LexWriter(wrnotn, renderset = rset)
        self.pwtrunk = TabWriter('html',
            lw = self.lwtrunk,
            classes = ['example', 'build-trunk'],
        )
        self.trunk_exarg = Notation.polish.Parser().argument('b', ('a1', 'a2'))

        # self.replace_defns = []
        self._listeners: dict[str, list] = defaultdict(list)
        self._connids = dict()

    # TODO: generate rule "cheat sheet"

    ## Doc Lines

    def lines_rule_example(self, rule: Rule|type[Rule], logic: Any = None, indent: str|int = None):
        'ReST lines (indented) for ``Rule`` example.'
        plines = self.html_rule_example(rule, logic = logic).split('\n')
        return indented(['Example:', ''] + rawblock(plines), indent)

    def lines_trunk_example(self, logic: Any, indent: str|int = None):
        'ReST lines (indented) for ``build_trunk`` example.'
        plines = self.html_trunk_example(logic).split('\n')
        return indented(['Example:', '', *rawblock(plines)], indent)

    def lines_logic_truth_tables(self, logic: Any, indent: str|int = None):
        'ReST lines (indented) for truth tables of all operators.'
        logic = get_logic(logic)
        m: BaseModel = logic.Model()
        tables = [
            self.html_truth_table(logic, oper)
            for oper in sorted(m.truth_functional_operators)
            # for operator in Operator
            # if operator in logic.Model.truth_functional_operators
        ]
        lines = '\n'.join(tables).split('\n')
        lines.append('<div class="clear"></div>')
        return rawblock(lines, indent)

    def lines_rule_docstring(self, rule:str|type[Rule], logic: Any = None, indent: str|int = None):
        'Docstring lines (stripped, indented) for a ``Rule`` class.'
        logic = get_logic(logic or rule)
        found: type[Rule] = None
        for name, member in inspect.getmembers(logic.TabRules):
            if name == rule or member == rule:
                found = member
                break
        else:
            raise RuleNotFoundError(f'{rule}, (logic: {logic.name})')
        lines = [line.strip() for line in found.__doc__.split('\n')]
        return indented(lines, indent)

    def lines_inherited_ruledoc(self, rule: type[Rule], indent: str|int = None):
        'Docstring lines (stripped, indented) for an "inheriting only" ``Rule`` class.'
        prule = getmro(rule)[1]
        plogic = get_logic(prule)
        lines = [
            f'*This rule is the same as* :class:`{plogic.name} {prule.__name__}',
            f'<{prule.__module__}.{prule.__qualname__}>`',
            '',
        ]
        lines.extend(self.lines_rule_docstring(prule, logic = plogic))
        # lines.extend(line.strip() for line in prule.__doc__.split('\n'))
        lines.append('')
        return indented(lines, indent)

    def lines_opers_table(self, indent: str|int = None):
        'ReST lines (indented) for the Operators reference table CSV data.'
        sympol, symstd = (
            {o: table.char(LexType.Operator, o) for o in Operator}
            for table in (
                ParseTable.fetch(Notation.polish),
                ParseTable.fetch(Notation.standard),
            )
        )
        symhtml, symunic = (
            {o: rset.strfor(o.TYPE, o) for o in Operator}
            for rset in (
                RenderSet.fetch(Notation.standard, 'html'),
                RenderSet.fetch(Notation.standard, 'unicode')
            )
        )
        # lwhtm = LexWriter('standard', charset = 'unicode')
        # symhtml = {
        #     # o: htmlun(lwhtm.write(o)) for o in oplist
        #     o: lwhtm.write(o) for o in oplist
        # }
        lines = [
            '"","","","Render only"',
            '"Operator Name","Polish","Standard","Standard HTML","Standard Unicode"',
        ] + [
            '"{0}","``{1}``","``{2}``","{3}","{4}"'.format(*row)
            for row in (
                (o, sympol[o], symstd[o], htmlun(symhtml[o]), symunic[o])
                for o in Operator
            )
        ]
        return indented(lines, indent)

    ## HTML Output

    def html_trunk_example(self, logic: Any) -> str:
        'HTML for argument and ``build_trunk`` example.'
        logic = get_logic(logic)
        # arg = parse_argument('b', ('a1', 'a2'), notn = 'polish')
        arg = self.trunk_exarg
        lw = self.lwtrunk
        pw = self.pwtrunk
        tab = Tableau(logic)
        # Pluck a rule.
        rule = tab.rules.groups[1][0]
        # Inject the helper.
        rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
        # Build trunk.
        tab.argument = arg
        tab.finish()
        # Render argument.
        prems = map(lw, arg.premises)
        conc = lw(arg.conclusion)
        if lw.charset != 'html':
            prems = map(htmlesc, prems)
            conc = htmlesc(conc)
        return cat(
            'Argument: <i>',
            '</i> ... <i>'.join(prems),
            f'</i> &there4; <i>{conc}</i>\n',
            pw(tab),
        )

    def html_rule_example(self, rule: Rule|type[Rule], logic: Any = None) -> str:
        "HTML for ``Rule`` example."
        logic = get_logic(logic or rule)
        tab = Tableau(logic)
        rule = tab.rules.get(rule)
        # TODO: fix for closure rules
        isclosure = isinstance(rule, ClosingRule)
        if not isclosure:
            rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
        pw = self.pwclosure if isclosure else self.pwrule
        b = tab.branch()
        b.extend(rule.example_nodes())
        rule.apply(rule.get_target(b))
        return pw(tab.finish())

    def html_truth_table(self, logic: Any, oper: str|Operator, classes: list[str] = []):
        'HTML for a truth table of ``oper``.'
        model: BaseModel = get_logic(logic).Model()
        oper = Operator[oper]
        table = model.truth_table(oper, reverse = self.opts['truth_tables_rev'])
        return self.TT_TEMPL.render(dict(
            num_values = len(model.Value),
            table      = table,
            operator   = oper,
            lw         = self.lw,
            classes    = list(classes),
        ))

    ## =========================
    ## Sphinx Event Handlers   :
    ## =========================

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    def connect_sphinx(self, app: Sphinx, event: str, *methods: str|Callable):
        """
        Attach a listener to a Sphinx event. We handle our own listeners so we
        can do proper error handling. Each of ``methods`` can be a function or
        name of a Helper method.  One handler per event is attached to Sphinx,
        which is a lambda wrapper for ``__dispatch_sphinx()``.
        """
        if event not in self._connids:
            logger.info(f'Creating dispatcher for {event}')
            dispatch = self.__dispatch_sphinx
            def dispatcher(*args):
                return dispatch(event, args)
            self._connids[event] = app.connect(event, dispatcher)
        append = self._listeners[event].append
        for f in methods:
            if isinstance(f, str):
                f = getattr(self, f)
            logger.info(f'Connecting {f.__name__} to {event}')
            append(f)
        return self

    def sphinx_regex_simple_replace_common(self, lines: list[str], is_source: bool = False):
        logicmatch = '|'.join(v.upper() for v in LOGICS)
        defns = (
            # Truth values
            (r'{v.([TBNF])}', ':math:`\\1`'),
            # Logic class links like :ref:`FDE`
            (
                r'{{@({0})}}'.format(logicmatch),
                lambda pat: (
                    ':class:`{0} <logics.{1}>`'.format(
                        pat.group(1), pat.group(1).lower()
                    )
                )
            ),
            # Meta-tuple params - :m:`ntuple`
            (':m:`ntuple`', ':math:`\\\\langle a_0,...,a_n\\\\rangle`'),
        )
        text = '\n'.join(lines)
        for regex, repl in defns:
            text = re.sub(regex, repl, text)
        if is_source:
            lines[0]= text
        else:
            lines.clear()
            lines.extend(text.split('\n'))

    def sphinx_regex_simple_replace_source(self, app: Sphinx, docname: str, lines: list[str]):
        self.sphinx_regex_simple_replace_common(lines, is_source = True)

    def sphinx_regex_simple_replace_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        self.sphinx_regex_simple_replace_common(lines, is_source = False)

    def sphinx_regex_line_replace_common(self, lines: list[str], is_source: bool = False):
        """
        Replace a line matching a regex with 1 or more lines. Lines could come
        from autodoc extraction or straight from source. In the latter case,
        it is important to observe correct indenting for new lines.

        This matches the first occurrence in a line and replaces that line with
        the line(s) returned. So these kinds of matches should generally be
        the only thing on a line.
        """
        defns = (
            # (
            #     '//ruledoc//',
            #     r'(\s*)//ruledoc//(.*?)//(.*)//',
            #     lambda indent, logic, rule: (
            #         self.lines_rule_docstring(rule, logic = logic, indent = indent)
            #     ),
            # ),
            (
                '//truth_tables//',
                r'(\s*)//truth_tables//(.*?)//',
                lambda indent, logic: (
                    self.lines_logic_truth_tables(logic, indent = indent)
                ),
            ),
            (
                '//lexsym_opers_csv//',
                r'(\s*)//lexsym_opers_csv//',
                self.lines_opers_table,
            )
        )
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
                    if isinstance(match, str):
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

    def sphinx_regex_line_replace_source(self, app: Sphinx, docname: str, lines: list[str]):
        'Replace a line matching a regex with 1 or more lines in a docstring.'
        self.sphinx_regex_line_replace_common(lines, is_source = True)

    def sphinx_regex_line_replace_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        'Regex line replace for autodoc event. Delegate to common method.'
        self.sphinx_regex_line_replace_common(lines, is_source = False)

    def sphinx_obj_lines_append_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        """Append lines to a docstring extracted from the autodoc extention.
        For injecting into doc source files, use a regex line replacement.
        """
        defns = (
            (
                self.should_inherit_ruledoc,
                self.lines_inherited_ruledoc,
            ),
            (
                Rule in safemro(obj) and obj not in self.SKIP_RULES,
                self.lines_rule_example,
            ),
            (
                TabSys.build_trunk in methmro(obj) and obj not in self.SKIP_TRUNKS,
                self.lines_trunk_example,
            )
        )
        for check, func in defns:
            if check and (not callable(check) or check(obj)):
                lines += func(obj)

    # def sphinx_evtest(self, app, domain, objtype, contentnode):
    #     #print('\n\n\n', (domain, objtype, contentnode), '\n')
    #     # if pagename == '_modules/logics/fde':
    #     #     for n in doctree.traverse():
    #     #         print(str(n.attlist()))
    #     # # print('\n\n\n', (pagename, templatename), '\n')
    #     pass



    ## Custom Roles

    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    #
    # > Role functions return a tuple of two values:
    # >
    # > - A list of nodes which will be inserted into the document tree at the
    # >   point where the interpreted role was encountered (can be an empty
    # >   list).
    # >
    # > - A list of system messages, which will be inserted into the document tree
    # >   immediately after the end of the current block (can also be empty).

    def rolemethod(func: F) -> F:
        'Temp decorator.'
        func.options = {'class': directives.class_option}
        func.content = True
        return func

    @rolemethod
    def role_lexrender_auto(self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner,
        opts: dict = {},
        content: list[str] = [], /
    ) -> tuple[list[docnodes.Node], list[str]]:
        try:
            return self._lexrender_common(text, opts)
        except Exception as e:
            logger.error(e)
            logger.error(f'role_lexrender_auto: rawtext={rawtext}, lineno={lineno}')
            logger.error('content=\n' + '\n'.join(content))
            raise e

    @rolemethod
    def role_lexrender_oper(self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner,
        opts: dict = {},
        content: list[str] = [], /
    ) -> tuple[list[docnodes.Node], list[str]]:
        try:
            return self._lexrender_common(text, opts, what = 'operator')
        except Exception as e:
            logger.error(e)
            logger.error(f'role_lexrender_oper: rawtext={rawtext}, lineno={lineno}')
            logger.error('content=\n' + '\n'.join(content))
            raise e

    def _lexrender_common(self,
        text: str,
        opts: dict,
        what: Any = None
    ) -> tuple[list[docnodes.Node], list[str]]:
        'Common lexrender routine.'
        classes = ['lexitem']
        item = None
        if not what:
            m = re.match(r'^(.)([0-9]*)$', text)
            if m:
                table = self.parser.table
                char, sub = m.groups()
                sub = int(sub) if len(sub) else 0
                ctype = table.type(char)
                if ctype in (LexType.Operator, LexType.Quantifier):
                    what, item = table[char]
                elif ctype in (LexType.Constant, LexType.Variable):
                    what, idx = table[char]
                    if ctype is LexType.Constant:
                        item = Constant(idx, sub)
                        classes.append('constant')
                    else:
                        item = Variable(idx, sub)
                        classes.append('variable')
                elif ctype is LexType.Predicate:
                    what = 'predicate'
                    _, idx = table[char]
                    item = self.opts['preds'].get((idx, sub))
                    classes.append('user_predicate')
                elif ctype is Predicate.System:
                    what = 'predicate'
                    _, item = table[char]
                    item = Predicate.System(item)
                    classes.extend(('system_predicate', item.name))
        if not what:
            what = 'sentence'
        if what == 'sentence':
            item = self.parser(text)
        if not item:
            item = text
        if not isinstance(what, str):
            what = type(item).__name__
        classes.append(what)
        raw = self.lw(item)
        rendered = htmlun(raw)
        node = docnodes.inline(text = rendered, classes = classes)
        set_classes(opts)
        return [node], []

    @rolemethod
    def role_lexrender_meta(self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner,
        opts: dict = {},
        content: list[str] = [], /
    ) -> tuple[list[docnodes.Node], list[str]]:
        classes = ['lexmeta']

        if text.upper() in ('P3', 'B3', 'G3', 'K3', 'L3', 'Ł3', 'RM3'):
            classes.append('subber')
            parts = list(text.upper())
            r = parts.pop(0) if len(parts) == 3 else None
            main, down = parts
            if r:
                main = r + main
            if main == 'L':
                main = 'Ł'
            nlist = [
                docnodes.inline(text = main, classes = classes + ['main']),
                docnodes.subscript(text = down, classes = classes + ['down']),
            ]
            return (nlist, [])

        if text.upper() in ('B3E', 'K3W', 'K3WQ'):
            # :math:`{B^E_3}`
            classes.append('subsup')
            parts = list(text.upper())
            q = parts.pop() if len(parts) == 4 else None
            main, up, down = parts
            if q:
                down += q
            nlist = [
                docnodes.inline(text = main, classes = classes + ['main']),
                docnodes.superscript(text = up, classes = classes + ['up']),
                docnodes.subscript(text = down, classes = classes + ['down']),
            ]
            # if q:
            #     nlist.append(
            #         docnodes.inline(text=q, classes = classes + ['post'])
            #     )
            return nlist, []

        nclass = docnodes.math
        attrs = {}
        bs = '\\'
        if text == 'ntuple':
            classes.extend(['tuple', 'ntuple'])
            rend = cat(bs, 'langle a_0,...,a_n', bs, 'rangle')
        elif text in ('T', 'F', 'N', 'B'):
            classes.extend(['truth-value'])
            rend = text
            nclass = docnodes.strong
        elif re.match(r'^w[0-9]', text):
            # w0 or w0Rw1
            wparts = text.split('R')
            rend = '\\mathcal{R}'.join(
                re.sub(r'w([0-9]+)', 'w_\\1', wtxt)
                for wtxt in wparts
            )
            classes.append('modal')#
            classes.append('access' if len(wparts) > 1 else 'world')
        elif text == 'w' or re.match(r'', text):
            # <w, w'> etc.
            if '<' in text:
                classes.append('tuple')
            rend = text.replace('<', '\\langle ').replace('>', '\\rangle')
            #rend = text.replace('<', '⟨').replace('>', '⟩')
            #nclass = docnodes.inline
            classes.extend(['modal'])

        else:
            if '.' in text:
                pfx, text = text.split('.', 1)
            else:
                raise UnknownLexTypeError(f'Unspecified metalexical type: {text}')
            if pfx == 'v':
                # truth-values
                # escape for safety
                rend = htmlesc(text)
            else:
                raise UnknownLexTypeError(f'Unknown metalexical type: {pfx}')
        node = nclass(text = rend, classes = classes, **attrs)
        # if ismath:
        #     node = docnodes.math(text = rend, classes=['fooclass'])
        # else:
        #     node = docnodes.inline(text = rend, classes=['fooclass'])
        set_classes(opts)
        return [node], []

    del(rolemethod)

    ## Dispatcher

    def __dispatch_sphinx(self, event: str, args: tuple):
        for func in self._listeners[event]:
            try:
                func(*args)
            except Exception as e:
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
    def should_inherit_ruledoc(self, rule: type[Rule]):
        """
        if a rule:
            - is included in TabRules groups for the module it belongs to
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

def rawblock(lines: list[str], indent: str|int = None) -> list[str]:
    'Make a raw html block from the lines. Returns a new list of lines.'
    return indented(
        ['.. raw:: html', '', *indented(lines, 4), ''],
        indent = indent,
    )

def indented(lines: list[str], indent: str|int = None) -> list[str]:
    'Indent non-empty lines. Indent can be string or number of spaces.'
    if indent is None:
        indent = ''
    elif isinstance(indent, int):
        indent *= ' '
    return [
        cat(indent, line) if len(line) else line
        for line in lines
    ]

def safemro(obj: Any) -> tuple[type, ...]:
    'Try to get the mro of the class, else empty list'
    try:
        return getmro(obj)
    except:
        return ()

def methmro(meth: Any) -> list[str]:
    """Get the methods of the same name of the mro (safe) of the class the method is bound to"""
    try:
        clsmro = getmro(meth.__self__)
        meths = [getattr(c, meth.__name__, None) for c in clsmro]
        return [m for m in meths if m]
    except:
        return []

def isnodoc(obj: Any) -> bool:
    return not bool(getattr(obj, '__doc__', None))

def isnocode(obj: Any) -> bool:
    'Try to determine if obj has no "effective" code.'
    try:
        lines = [
            line
            for line in (
                line.strip()
                for line in getsource(obj).split('\n')
             ) if line
        ]
        isblock = False
        isfirst = True
        for line in lines:
            if isfirst:
                isfirst = False
                regex = r'^(class|def) {0}(\([a-zA-Z0-9_.]+\))?:$'.format(obj.__name__)
                m = re.findall(regex, line)
                if not m:
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
            return False
        return True
    except:
        # raise
        return False

def rulegrouped(rule, logic) -> bool:
    if Rule not in safemro(rule):
        return False
    try:
        logic = get_logic(logic)
        rcls = logic.TabRules
        if rule in rcls.closure_rules:
            return True
        for grp in rcls.rule_groups:
            if rule in grp:
                return True
        return False
    except:
        return False

def selfgrouped(rule) -> bool:
    try:
        return rulegrouped(rule, get_logic(rule))
    except:
        return False

def parentgrouped(rule) -> bool:
    try:
        parent = getmro(rule)[1]
        plgc = get_logic(parent)
        return rulegrouped(parent, plgc)
    except:
        return False

def set_classes(options: dict):
    """Set options['classes'] and delete options['class'].

    From: https://github.com/docutils-mirror/docutils/blob/master/docutils/parsers/rst/roles.py#L385
    """
    if 'class' in options:
        if 'classes' in options:
            raise KeyError("classes")
        options['classes'] = options['class']
        del options['class']

class BadExpressionError(ValueError):
    pass

class RuleNotFoundError(ValueError):
    pass

class UnknownLexTypeError(ValueError):
    pass


# class ParseRenderDirective(Directive):
#     sp = create_parser(
#         notation = 'standard',
#         preds = examples.preds,
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
#         node = docnodes.inline(text=self.sw.write(self.sp.parse('A V ~A')))
#         return [node]
# def sphinx_filter_signature(self, app, what, name, obj, options, signature, return_annotation):
#     raise NotImplementedError()
#     if what == 'class' and name.startswith('logics.') and '.TabRules.' in name:
#         # check if it is in use in rule groups
#         logic = get_logic(obj)
#         isfound = False
#         if obj in logic.TabRules.closure_rules:
#             print('CLUSRE', name, logic.name)
#             isfound = True
#         if not isfound:
#             for grp in logic.TabRules.rule_groups:
#                 if obj in grp:
#                     print('Found', name, logic.name)
#                     isfound = True
#                     break
#         if not isfound:
#             print('NOTFOUND', name, logic.name)
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