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
from errors import instcheck

__all__ = 'Helper',

import examples
from lexicals import (
    Constant,
    LexType,
    LexWriter,
    Notation,
    Operator,
    Parser,
    ParseTable,
    Predicate,
    RenderSet,
    Variable,
)
from logics import fde as FDE
from models import BaseModel
from proof.helpers import EllipsisExampleHelper
from proof.tableaux import (
    ClosingRule,
    Tableau,
    TableauxSystem as TabSys,
    Rule,
)
from proof.writers import TabWriter
from tools.abcs import (
    F,
    MapProxy,
    closure,
)
from tools.decorators import (
    overload,
    wraps
)
from tools.misc import (
    cat,
    get_logic,
)

from collections import defaultdict
from docutils import nodes as docnodes
import docutils.parsers.rst.directives as directives
from html import (
    escape as htmlesc,
    unescape as htmlun,
)
from inspect import (
    getmro,
    getsource,
)
from jinja2 import (
    Environment,
    FileSystemLoader,
)
import os
from os.path import (
    abspath,
    basename as bname,
    join as pjoin,
)
import re
from sphinx.application import Sphinx
from sphinx.util import logging
import traceback
from typing import (
    Any,
    Callable,
)

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


logger = logging.getLogger(__name__)

# From: https://docutils.sourceforge.io/docs/howto/rst-roles.html
#
# > Role functions return a tuple of two values:
# >
# > - A list of nodes which will be inserted into the document tree at the
# >   point where the interpreted role was encountered (can be an empty
# >   list).
# >
# > - A list of system messages, which will be inserted into the document tree
# >   immediately after the end of the current block (can also be empty).
_RoleRet = tuple[list[docnodes.Node], list[str]]

class Helper:

    _defaults = MapProxy(dict(
        doc_dir          = abspath(pjoin(os.path.dirname(__file__), '../doc')),
        logics_doc_dir   = 'logics',
        template_dir     = 'templates',
        truth_table_tmpl = 'truth_table.jinja2',
        truth_tables_rev = True,
        write_notation   = Notation.standard,
        parse_notation   = Notation.standard,
        preds            = examples.preds,
    ))

    @staticmethod
    def setup_sphinx(app: Sphinx, opts: dict) -> Helper:

        helper = Helper(opts)

        helper.connect_sphinx(app, 'autodoc-process-docstring',
            helper.sphinx_obj_lines_append_autodoc,
            helper.sphinx_regex_line_replace_autodoc,
            helper.sphinx_regex_simple_replace_autodoc,
        )

        helper.connect_sphinx(app, 'source-read',
            helper.sphinx_regex_line_replace_source,
            helper.sphinx_regex_simple_replace_source,
        )

        app.add_role('s', helper.role_lexrender_auto)
        app.add_role('oper', helper.role_lexrender_oper)
        app.add_role('m', helper.role_lexrender_meta)

        return helper

    # Don't build rules for abstract classes
    # TODO: shouldn't this check rule groups?
    SKIP_RULES = (
        Rule,
        ClosingRule,
    )
    SKIP_TRUNKS = (
        TabSys.build_trunk,
    )
    TRUNK_ARG = Parser('polish').argument('b', ('a1', 'a2'))
    DIV_CLEAR = '<div class="clear"></div>'

    def __init__(self, opts: dict = {}):

        self.opts = opts = dict(self._defaults) | opts

        self.logic_names = tuple(
            bname('.'.join(file.split('.')[0:-1])).upper()
            for file in os.listdir(
                pjoin(opts['doc_dir'], opts['logics_doc_dir'])
            )
            if file.endswith('.rst')
        )
        self.jenv = Environment(
            loader = FileSystemLoader(
                pjoin(opts['doc_dir'], opts['template_dir'])
            ),
            trim_blocks = True,
            lstrip_blocks = True,
        )

        self.parser = Parser(
            opts['parse_notation'],
            opts['preds'],
        )

        lwnotn = Notation(opts['write_notation'])
        self.lwhtml = LexWriter(lwnotn, 'html')

        rskey = 'docutil.trunk'
        try:
            rstrunk = RenderSet.fetch(lwnotn, rskey)
        except KeyError:
            rshtml = RenderSet.fetch(lwnotn, 'html')
            rstrunk = RenderSet.load(lwnotn, rskey, dict(rshtml.data,
                name = f'{lwnotn.name}.{rskey}',
                renders = dict(rshtml.renders,
                    subscript = lambda sub: (
                        '<sub>%s</sub>' % ('n' if sub == 2 else sub)
                    )
                )
            ))

        self.pwrule = TabWriter('html',
            lw = self.lwhtml,
            classes = ('example', 'rule'),
        )
        self.pwclosure = TabWriter('html',
            lw = self.lwhtml,
            classes = ('example', 'rule', 'closure'),
        )
        self.pwtrunk = TabWriter('html',
            lw = LexWriter(lwnotn, renderset = rstrunk),
            classes = ('example', 'build-trunk'),
        )

        self._listeners: dict[str, list] = defaultdict(list)
        self._connids = {}

    # TODO: generate rule "cheat sheet"

    ## Doc Lines

    def lines_rule_example(self, rule: Rule|type[Rule], logic: Any = None, indent: str|int = None):
        'ReST lines for ``Rule`` example.'
        lines = ['Example:', '']
        lines.extend(
            rawblock(self.html_rule_example(rule, logic).split('\n'))
        )
        return indented(lines, indent)

    def lines_trunk_example(self, logic: Any, indent: str|int = None):
        'ReST lines for ``build_trunk`` example.'
        lines = ['Example:', '']
        lines.extend(
            rawblock(self.html_trunk_example(logic).split('\n'))
        )
        return indented(lines, indent)

    def lines_logic_truth_tables(self, logic: Any, indent: str|int = None):
        'ReST lines for truth tables of all operators.'
        logic = get_logic(logic)
        m: BaseModel = logic.Model()
        lines = [
            line
            for oper in sorted(m.truth_functional_operators)
                for line in self.html_truth_table(logic, oper).split('\n')
        ]
        lines.append(self.DIV_CLEAR)
        return rawblock(lines, indent)

    def lines_inherited_ruledoc(self, rule: type[Rule], indent: str|int = None):
        'Docstring lines for an "inheriting only" ``Rule`` class.'
        prule = getmro(rule)[1]
        plogic = get_logic(prule)
        lines = [
            f'*This rule is the same as* :class:`{plogic.name} {prule.__name__}',
            f'<{prule.__module__}.{prule.__qualname__}>`',
            '',
        ]
        lines.extend(line.strip() for line in prule.__doc__.split('\n'))
        lines.append('')
        return indented(lines, indent)

    def lines_opers_table(self, indent: str|int = None):
        'ReST lines for the Operators table CSV data.'
        charpol, charstd = (
            {o: table.char(o.TYPE, o) for o in Operator}
            for table in (
                ParseTable.fetch(Notation.polish),
                ParseTable.fetch(Notation.standard),
            )
        )
        strhtml, strunic = (
            {o: rset.string(o.TYPE, o) for o in Operator}
            for rset in (
                RenderSet.fetch(Notation.standard, 'html'),
                RenderSet.fetch(Notation.standard, 'unicode'),
            )
        )
        lines = [
            '"",' * 3                       + '"Render only"',
            '"Operator", "Polish", "Standard", "Std. HTML", "Std. Unicode"',
        ]
        lines.extend(
            f'"{o}", "``{charpol[o]}``", "``{charstd[o]}``", '
            f'"{htmlun(strhtml[o])}", "{strunic[o]}"'
            for o in Operator
            # for row in (
            #     (o, charpol[o], charstd[o], htmlun(strhtml[o]), strunic[o])
            #     for o in Operator
            # )
        )
        return indented(lines, indent)

    ## HTML Output

    def html_trunk_example(self, logic: Any) -> str:
        'HTML for argument and ``build_trunk`` example.'
        logic = get_logic(logic)
        tab = Tableau(logic)
        # Pluck a rule.
        rule = tab.rules.groups[1][0]
        # Inject the helper.
        rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
        # Build trunk.
        tab.argument = arg = self.TRUNK_ARG
        tab.finish()
        # Render argument.
        pw = self.pwtrunk
        lw = pw.lw
        prems = map(lw, arg.premises)
        conc = lw(arg.conclusion)
        if lw.charset != 'html':
            prems = map(htmlesc, prems)
            conc = htmlesc(conc)
        pstr = '</i> ... <i>'.join(prems)
        return f'Argument: <i>{pstr}</i> &there4; <i>{conc}</i>\n{pw(tab)}'

    def html_rule_example(self, rule: Rule|type[Rule], logic: Any = None) -> str:
        "HTML for ``Rule`` example."
        logic = get_logic(logic or rule)
        tab = Tableau(logic)
        rule = tab.rules.get(rule)
        # TODO: fix for closure rules
        if isinstance(rule, ClosingRule):
            pw = self.pwclosure
        else:
            pw = self.pwrule
            rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
        b = tab.branch()
        b.extend(rule.example_nodes())
        rule.apply(rule.target(b))
        tab.finish()
        return pw(tab)

    def html_truth_table(self, logic: Any, oper: str|Operator) -> str:
        'HTML for a truth table of ``oper``.'
        model: BaseModel = get_logic(logic).Model()
        oper = Operator[oper]
        opts = self.opts
        table = model.truth_table(oper, reverse = opts['truth_tables_rev'])
        template = self.jenv.get_template(opts['truth_table_tmpl'])
        return template.render(dict(
            num_values = len(model.Value),
            table      = table,
            operator   = oper,
            lw         = self.lwhtml,
        ))

    ## Sphinx Event Handlers

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    def connect_sphinx(self, app: Sphinx, event: str, *methods: str|Callable):
        """Attach a listener to a Sphinx event. Each of ``methods`` can be a function
        or ``Helper`` method name.
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
            append(instcheck(f, Callable))

    def sphinx_regex_simple_replace_common(self, lines: list[str], is_source: bool = False):
        logicmatch = '|'.join(self.logic_names)
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
        if is_source:
            proclines = lines[0].split('\n')
        else:
            proclines = lines
        i = 0
        rpl = {}
        for line in proclines:
            for indic, regex, func in defns:
                if indic in line:
                    matches = re.findall(regex, line)
                    if not matches:
                        raise ValueError(f"Bad expression: {repr(line)}")
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
            lines[0] = '\n'.join(proclines)

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


    ## Custom Sphinx Roles

    @staticmethod
    @overload
    def sphinxrole(func: F, /) -> F: ...

    @staticmethod
    @overload
    def sphinxrole(*, keyed: bool = True, content: bool = True, options: dict = {}) -> Callable[[F], F]: ...

    @staticmethod
    def sphinxrole(func = None, /, **kw):
        'Decorator/factory for Sphinx role method.'

        def decorator(func: F) -> F:
            fopts = dict(keyed = True, content = True, options = {})
            fopts.update(kw)
            @wraps(func)
            def f(self, name: str, rawtext: str, text: str, lineno: int,
                inliner, opts: dict = {}, content: list[str] = [], /):
                kwargs = dict(
                    name = name, rawtext = rawtext, text = text, lineno = lineno,
                    inliner = inliner, opts = opts, content = content
                )
                set_classes(opts)
                try:
                    if fopts['keyed']:
                        ret = func(self, **kwargs)
                    else:
                        ret = func(self, *kwargs.values())
                except:
                    logger.error(
                        f"{func.__name__}: lineno={lineno}, "
                        f"rawtext={repr(rawtext)}, content={content}"
                    )
                    logger.info('Printing traceback')
                    traceback.print_exc()
                    raise
                else:
                    if not isinstance(ret, tuple):
                        ret = ret, []
                    return ret
            f.options = {'class': directives.class_option} | fopts['options']
            f.content = fopts['content']
            _RoleRet # fail if missing
            f.__annotations__['return'] = '_RoleRet'
            return f

        if func is None:
            return decorator

        if len(kw):
            raise TypeError('Unexpected kwargs with `func` parameter')

        return decorator(instcheck(func, Callable))

    @sphinxrole
    def role_lexrender_auto(self, /, *, text: str, opts: dict, **_):
        return self._lexrender_common(text, opts)
        # try:
        #     return self._lexrender_common(text, opts)
        # except Exception as e:
        #     logger.error(e)
        #     logger.error(f'role_lexrender_auto: rawtext={rawtext}, lineno={lineno}')
        #     logger.error('content=\n' + '\n'.join(content))
        #     raise e

    @sphinxrole
    def role_lexrender_oper(self, /, *, text: str, opts: dict, **_):
        return self._lexrender_common(text, opts, 'operator')
        # try:
        #     return self._lexrender_common(text, opts, what = 'operator')
        # except Exception as e:
        #     logger.error(e)
        #     logger.error(f'role_lexrender_oper: rawtext={rawtext}, lineno={lineno}')
        #     logger.error('content=\n' + '\n'.join(content))
        #     raise e

    def _lexrender_common(self, text: str, opts: dict, what: Any = None, /):
        'Common lexrender routine.'
        classes = ['lexitem']
        item = None
        if what is None:
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
        if what is None:
            what = 'sentence'
        if what == 'sentence':
            item = self.parser(text)
        if item is None:
            item = text
        if not isinstance(what, str):
            what = type(item).__name__
        classes.append(what)
        raw = self.lwhtml(item)
        rendered = htmlun(raw)
        return [
            docnodes.inline(text = rendered, classes = classes)
        ]

    @sphinxrole
    @closure
    def role_lexrender_meta():
        LANGLE = '\\langle'
        RANGLE = '\\rangle'

        from logics import fde as FDE

        _sets = dict(
            subber = {'P3', 'B3', 'G3', 'K3', 'L3', 'Ł3', 'RM3'},
            subsup = {'B3E', 'K3W', 'K3WQ'},
            truthvals = {'T', 'F', 'N', 'B'},
            # truthvals = FDE.Model.Value,
        )

        def role(self: Helper, /, *, text: str, **_):

            classes = ['lexmeta']

            textuc = text.upper()

            if textuc in _sets['subber']:#('P3', 'B3', 'G3', 'K3', 'L3', 'Ł3', 'RM3'):
                classes.append('subber')
                main, down = textuc[0:2]
                if len(text) == 3:
                    main = textuc[2] + main
                if main == 'L':
                    main = 'Ł'
                return [
                    docnodes.inline(text = main, classes = classes + ['main']),
                    docnodes.subscript(text = down, classes = classes + ['down']),
                ]

            if textuc in _sets['subsup']:#('B3E', 'K3W', 'K3WQ'):
                # :math:`{B^E_3}`
                classes.append('subsup')
                main, up, down = textuc[0:3]
                if len(text) == 4:
                    down += textuc[3]
                return [
                    docnodes.inline(text = main, classes = classes + ['main']),
                    docnodes.superscript(text = up, classes = classes + ['up']),
                    docnodes.subscript(text = down, classes = classes + ['down']),
                ]


            if text == 'ntuple':
                # n-tuple.
                classes.extend(('tuple', 'ntuple'))
                rendered = f'{LANGLE} a_0,...,a_n{RANGLE}'
                return [
                    docnodes.math(text = rendered, classes = classes)
                ]

            # if text in FDE.Model.Value:
            if text in _sets['truthvals']:#('T', 'F', 'N', 'B'):
                assert text in {'T', 'F', 'N', 'B'} # sanity
                # Truth values.
                classes.append('truth-value')
                return [
                    docnodes.strong(text = text, classes = classes)
                ]

            if re.match(r'^w[0-9]', text):
                # w0 or w0Rw1
                classes.append('modal')
                parts = text.split('R')
                if len(parts) > 1:
                    classes.append('access')
                else:
                    classes.append('world')
                # insert underscore
                parts = [re.sub(r'w([0-9]+)', 'w_\\1', n) for n in parts]
                # rejoin with R
                rendered = '\\mathcal{R}'.join(parts)
                return [
                    docnodes.math(text = rendered, classes = classes)
                ]

            if text == 'w' or re.match(r'', text):
                # <w, w'> etc.
                classes.append('modal')
                if '<' in text:
                    classes.append('tuple')
                rendered = text.replace('<', f'{LANGLE} ').replace('>', RANGLE)
                #rendered = text.replace('<', '⟨').replace('>', '⟩')
                #nodecls = docnodes.inline
                return [
                    docnodes.math(text = rendered, classes = classes)
                ]

            raise ValueError(f"Unrecognized meta-lexical text '{text}'")

        return role

    ## Dispatcher

    def __dispatch_sphinx(self, event: str, args: tuple):
        'Consolidated Sphinx event dispatcher.'
        for func in self._listeners[event]:
            try:
                func(*args)
            except:
                # if event == 'autodoc-process-docstring' and len(args) > 2:
                #     arginfo = str({'what': args[1], 'name': args[2]})
                # elif event == 'source-read' and len(args) > 2:
                #     arginfo = '\n'.join((
                #         '',
                #         'docname: {0}\n'.format(args[1]),
                #         'content: \n\n{0}'.format('\n'.join(args[2])),
                #     ))
                # else:
                #     arginfo = str(args)
                logger.error(
                    f"Event '{event}' failed for {func} with args {args}",
                )
                logger.info('Printing traceback')
                traceback.print_exc()
                raise

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
            isnodoc(rule) and
            isnocode(rule) and
            selfgrouped(rule) and
            parentgrouped(rule)
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

def isrulecls(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, Rule)

def rulegrouped(rule: type[Rule], logic: Any) -> bool:
    'Whether the Rule class is grouped in the TabRules of the given logic.'
    if not isrulecls(rule):
        return False
    try:
        logic = get_logic(logic)
    except:
        return False
    tabrules = logic.TabRules
    if rule in tabrules.closure_rules:
        return True
    for grp in tabrules.rule_groups:
        if rule in grp:
            return True
    return False

def selfgrouped(rule: type[Rule]) -> bool:
    'Whether the Rule class is grouped in the TabRules of its own logic.'
    return rulegrouped(rule, rule)

def parentgrouped(rule: type[Rule]) -> bool:
    "Whether the Rule class's parent is grouped in its own logic."
    if not isinstance(rule, type):
        return False
    return selfgrouped(rule.mro()[1])
    # try:
    #     parent = getmro(rule)[1]
    #     plgc = get_logic(parent)
    #     return rulegrouped(parent, plgc)
    # except:
    #     return False

def set_classes(options: dict):
    """Set options['classes'] and delete options['class'].

    From: https://github.com/docutils-mirror/docutils/blob/master/docutils/parsers/rst/roles.py#L385
    """
    if 'class' in options:
        if 'classes' in options:
            raise KeyError("classes")
        options['classes'] = options['class']
        del options['class']


# helper.connect_sphinx(app, 'autodoc-process-signature',
#     'sphinx_filter_signature',
# )

# helper.connect_sphinx(app, 'build-finished',

# )

# helper.connect_sphinx(app, 'object-description-transform',
#     'sphinx_evtest',
# )

# def sphinx_evtest(self, app, domain, objtype, contentnode):
#     #print('\n\n\n', (domain, objtype, contentnode), '\n')
#     # if pagename == '_modules/logics/fde':
#     #     for n in doctree.traverse():
#     #         print(str(n.attlist()))
#     # # print('\n\n\n', (pagename, templatename), '\n')
#     pass

# class ParseRenderDirective(Directive):
#     sp = Parser('standard', examples.preds)
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