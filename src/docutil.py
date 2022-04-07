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

__all__ = 'Helper',

from errors import instcheck
import examples
from lexicals import (
    LexType,
    LexWriter,
    Notation,
    Operator,
    Parser,
    ParseTable,
    Predicate,
    RenderSet,
    # Sentence,
)
from models import BaseModel
from proof.helpers import EllipsisExampleHelper
from proof.tableaux import (
    ClosingRule,
    Rule,
    Tableau,
    TableauxSystem as TabSys,
)
from tools.abcs import F, MapProxy
from tools.decorators import closure, overload, wraps
from tools.hybrids import qsetf
from tools.misc import get_logic

from collections import defaultdict
from docutils import nodes as docnodes
# import docutils.parsers.rst.directives as directives
from html import (
    escape as htmlesc,
    unescape as htmlun,
)
from inspect import getsource
import os
import re
from sphinx.application import Sphinx
from sphinx.util import logging
import traceback
from typing import Any, Callable

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
# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html


logger = logging.getLogger(__name__)
doc_suffix = '.rst'
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

Metawrite = {
    'prefixes' : {
        'L': 'logic_name',
        'V': 'truth_value',
        '!': 'fixed',
    },
}
Metawrite.update({
    'patterns': {
        'prefixed': r'(?P<raw>(?P<prefix>[%s]){(?P<value>.*?)})' % (
            re.escape(''.join(Metawrite['prefixes'].keys()))
        ),
    },
})
Metawrite['patterns'].update({
    'prefixed_role': '^%s$' % Metawrite['patterns']['prefixed']
})
Metawrite.update({
    'modes': {
        'fixed': {
            'ntuple': {
                'rend': '\\langle a_0,...,a_n\\rangle',
                'classes': ('tuple', 'ntuple'),
            },
        },
        'logic_name': {
            'match': {
                r'^(?:(?P<main>B|G|K|L|Ł|P|RM)(?P<down>3))$' : ('subber',),
                r'^(?:(?P<main>B)(?P<up>3)(?P<down>E))$'  : ('subsup',),
                r'^(?:(?P<main>K)(?P<up>3)(?P<down>WQ?))$': ('subsup',),
                # r'^(?P<name>(?P<main>B|K)(?P<up>3)(?P<down>E|WQ?))$': 'subsup',
                #{'B3E', 'K3W', 'K3WQ'},
                # r'^(B|K)3E|3(?P<down>WQ?)$': 'subsup',
            },
            'nodecls': docnodes.inline,
            'nodecls_map': {
                'main': docnodes.inline,
                'up'  : docnodes.superscript,
                'down': docnodes.subscript
            },
        },
        'truth_value': {
            'nodecls': docnodes.strong,
        },
        # Regex rewrite.
        'rewrite': {
            r'^(?:([a-zA-Z])-)?ntuple$': {
                'rep': lambda m, a='a': (
                    f'\\langle {m[1] or a}_0,...,{m[1] or a}_n\\rangle'
                ),
                'classes': ('tuple', 'ntuple'),
                'nodecls': docnodes.math,
            },
            r'^(w)([0-9]+)$': {
                'rep': r'\1_\2',
                'classes': ('modal', 'world'),
                'nodecls': docnodes.math,
            }
        },
    },
    'generic': {
        # Math symbol replace.
        'math_symbols': {
            r'<': re.escape('\\langle '),
            r'>': re.escape('\\rangle'),
        }
    },
})


class Helper:

    _defaults = MapProxy(dict(
        template_dir     = 'templates',
        truth_table_tmpl = 'truth_table.jinja2',
        truth_tables_rev = True,
        write_notation   = Notation.standard,
        parse_notation   = Notation.standard,
        preds            = examples.preds,
        lexwrite_roles   = ('s',),
        metawrite_roles  = ('m',),
    ))

    @staticmethod
    def setup_sphinx(app: Sphinx, **opts) -> Helper:

        helper = Helper(**opts)
        opts = helper.opts

        Include = include_directive(app)
        app.add_directive('include', Include, override = True)

        helper.connect_sphinx(app, 'autodoc-process-docstring',
            helper.sphinx_obj_lines_append_autodoc,
            helper.sphinx_line_replace_autodoc,
            helper.sphinx_simple_replace_autodoc,
        )

        helper.connect_sphinx(app, 'source-read',
            helper.sphinx_line_replace_source,
            helper.sphinx_simple_replace_source,
        )

        helper.connect_sphinx(app, 'include-read',
            helper.sphinx_line_replace_include,
            helper.sphinx_simple_replace_include,
        )

        for name in opts['lexwrite_roles']:
            app.add_role(name, helper.role_lexwrite)
        for name in opts['metawrite_roles']:
            app.add_role(name, helper.role_metawrite)
     
        return helper


    DIV_CLEAR = '<div class="clear"></div>'

    doc_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../doc')
    )
    logic_docpath = os.path.join(doc_dir, 'logics')
    logic_names = qsetf(
        os.path.basename(file).removesuffix(doc_suffix).upper()
        for file in os.listdir(logic_docpath)
        if file.endswith(doc_suffix)
    )
    logic_union = '|'.join(sorted(logic_names, key = len, reverse = True))

    def __init__(self, **opts):

        from proof.writers import TabWriter
        import jinja2

        self.opts = opts = dict(self._defaults) | opts

        instcheck(opts['metawrite_roles'], tuple)

        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(
                os.path.join(self.doc_dir, opts['template_dir'])
            ),
            trim_blocks = True,
            lstrip_blocks = True,
        )

        self.parser = Parser(opts['parse_notation'], opts['preds'])

        lwnotn = Notation(opts['write_notation'])
        self.lwhtml = LexWriter(lwnotn, 'html')

        self.pwrule = TabWriter('html',
            lw = self.lwhtml,
            classes = ('example', 'rule'),
        )
        self.pwclosure = TabWriter('html',
            lw = self.lwhtml,
            classes = ('example', 'rule', 'closure'),
        )

        # Make a RenderSet that renders subscript 2 as n.
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

    def lines_truth_tables(self, logic: Any, indent: str|int = None):
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

    def lines_ruledoc_inherit(self, rule: type[Rule], indent: str|int = None):
        'Docstring lines for an "inheriting only" ``Rule`` class.'
        prule = rule.mro()[1]
        plogic = get_logic(prule)
        lines = [
            f'*This rule is the same as* :class:`{plogic.name} {prule.__name__}',
            f'<{prule.__module__}.{prule.__qualname__}>`',
            '',
        ]
        lines.extend(map(str.strip, prule.__doc__.split('\n')))
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
        tab.argument = arg = Parser('polish').argument('b', ('a1', 'a2'))
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
        return template.render(dict(table = table, lw = self.lwhtml))

    ## Sphinx Event Handlers

    def connect_sphinx(self, app: Sphinx, event: str, *methods: str|Callable):
        """Attach a listener to a Sphinx event. Each of ``methods`` can be a function
        or ``Helper`` method name.
        """
        if event not in self._connids:
            logger.info(f'Creating dispatcher for {event}')
            dispatch = self._dispatch_sphinx
            def dispatcher(*args):
                return dispatch(event, args)
            self._connids[event] = app.connect(event, dispatcher)
        append = self._listeners[event].append
        for f in methods:
            if isinstance(f, str):
                f = getattr(self, f)
            logger.info(f'Connecting {f.__name__} to {event}')
            append(instcheck(f, Callable))

    # See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    def sphinx_simple_replace_source(self, app: Sphinx, docname: str, lines: list[str]):
        'Regex replace in a docstring using ``re.sub()``.'
        self._simple_replace_common(lines, mode = 'source')

    def sphinx_simple_replace_include(self, app: Sphinx, lines: list[str]):
        'Regex replace for custom include-read event.'
        self._simple_replace_common(lines, mode = 'include')

    def sphinx_simple_replace_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        'Regex replace for autodoc event.'
        self._simple_replace_common(lines)

    def sphinx_line_replace_source(self, app: Sphinx, docname: str, lines: list[str]):
        'Replace a line matching a regex with 1 or more lines in a docstring.'
        self._line_replace_common(lines, mode = 'source')

    def sphinx_line_replace_include(self, app: Sphinx, lines: list[str]):
        'Regex line replace for custom include-read event.'
        self._line_replace_common(lines, mode = 'include')

    def sphinx_line_replace_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        'Regex line replace for autodoc event.'
        self._line_replace_common(lines)

    def sphinx_obj_lines_append_autodoc(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
        """Append lines to a docstring extracted from the autodoc extention.
        For injecting into doc source files, use a regex line replacement.
        """
        defns = (
            (
                self._should_ruledoc_inherit,
                self.lines_ruledoc_inherit,
            ),
            (
                self._should_rule_example,
                self.lines_rule_example,
            ),
            (
                self._should_trunk_example,
                self.lines_trunk_example,
            )
        )
        for check, func in defns:
            if check(obj):
                lines += func(obj)

    _simple_replace = None
    _line_replace   = None

    @closure
    def _simple_replace_common():

        def logic_ref(match: re.Match):
            matchd = match.groupdict()
            name = matchd['name']
            sect: str|None = matchd['sect']
            anchor: str|None = matchd['anchor']
            if sect is None:
                title = name
            else:
                title = f'{name} {sect}'.strip()
            if anchor is None:
                if sect is None:
                    slug = name
                else:
                    #   `FDE truth tables <fde-truth-tables>`
                    slug = '-'.join(re.split(r'\s+', title.lower()))
                anchor = f'<{slug}>'
            return f":ref:`{title} {anchor}`"
            # name: str = match.group(1)
            # sect: str|None = match.group(2)
            # if sect is None:
            #     anchor = title = name
            # else:
            #     anchor = f'{name}-{sect.strip()}'.lower()
            #     title = f'{name}{sect}'
            # return f":ref:`{title} <{anchor}>`"

        def getdefns(self: Helper):
            defns = self._simple_replace
            if defns is not None:
                return defns

            opts = self.opts
            # metawrite_name = opts['metawrite_roles'][0]

            # def metawrite_wrap(match: re.Match):
            #     return f"{match[1]}:{metawrite_name}:`{match[2]}`"

            rolemap = {
                # regex: rolename
                Metawrite['patterns']['prefixed']: opts['metawrite_roles'][0]
            }
            defns = tuple(
                (r'(?<!`)' + pat, name)
                for pat, name in rolemap.items()
            )
            defns = (
                # Wrap to metawrite role
                (r'(?<!`)' + Metawrite['patterns']['prefixed'], r':%s:`\1`' % opts['metawrite_roles'][0]),
                # Link to a logic:
                #   {@K3}        -> :ref:`K3 <K3>`
                #   {@FDE Model} -> :ref:`FDE Model <fde-model>`
                # (r'{@(%s)([ A-Za-z-]+)?}' % self.logic_union, logic_ref),
                (r'{@(?P<name>%s)(?:\s+(?P<sect>[\sa-zA-Z-]+)?(?P<anchor><.*?>)?)?}' % self.logic_union, logic_ref),
            )

            self._simple_replace = defns
            return defns

        def common(self: Helper, lines: list[str], mode: str = None):
            defns = getdefns(self)
            rend = '\n'.join(lines)
            count = 0
            for pat, rep in defns:
                rend, num = re.subn(pat, rep, rend)
                count += num
            if count:
                if mode == 'source':
                    lines[0]= rend
                else:
                    lines.clear()
                    lines.extend(rend.split('\n'))

        return common

    @closure
    def _line_replace_common():

        def getdefns(self: Helper):

            defns = self._line_replace
            if defns is not None:
                return defns

            def truthtable(indent, logic):
                return self.lines_truth_tables(logic, indent)

            defns = (
                (
                    '//truth_tables//',
                    re.compile(r'(\s*)//truth_tables//(.*?)//'),
                    truthtable,
                ),
                (
                    '//lexsym_opers_csv//',
                    re.compile(r'(\s*)//lexsym_opers_csv//'),
                    self.lines_opers_table,
                )
            )

            self._line_replace = defns
            return defns

        def common(self: Helper, lines: list[str], mode:str = None):
            """
            Replace a line matching a regex with 1 or more lines. Lines could come
            from autodoc extraction or straight from source. In the latter case,
            it is important to observe correct indenting for new lines.

            This matches the first occurrence in a line and replaces that line with
            the line(s) returned. So these kinds of matches should generally be
            the only thing on a line.
            """
            defns = getdefns(self)
            if mode == 'source':
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
            if rpl and mode == 'source':
                lines[0] = '\n'.join(proclines)

        return common

    ## Custom Sphinx Roles

    @staticmethod
    @overload
    def sphinxrole(func: F, /) -> F: ...

    @staticmethod
    @overload
    def sphinxrole(*,
        keyed: bool = True, content: bool = True, options: dict = {},
    ) -> Callable[[F], F]: ...

    @staticmethod
    def sphinxrole(func = None, /, **kw):
        'Decorator/factory for Sphinx role method.'

        def decorator(func: F) -> F:

            @wraps(func)
            def f(self, name: str, rawtext: str, text: str, lineno: int,
                inliner, opts: dict = {}, content: list[str] = [], /):
                kwargs = dict(
                    name = name, rawtext = rawtext, text = text, lineno = lineno,
                    inliner = inliner, opts = opts, content = content
                )
                try:
                    ret = func(self, **kwargs)
                except:
                    logger.error(
                        f"{func.__name__}: rawtext={repr(rawtext)}, "
                        f"content={content}"
                    )
                    logger.info('Printing traceback')
                    traceback.print_exc()
                    raise
                else:
                    if isinstance(ret, docnodes.Node):
                        ret = [ret], []
                    elif not isinstance(ret, tuple):
                        ret = ret, []
                    return ret

            fopts = dict(content = True, options = {})
            fopts.update(kw)
            for name, value in fopts.items():
                setattr(f, name, value)

            _RoleRet # fail if missing
            f.__annotations__['return'] = '_RoleRet'

            return f

        if func is None:
            return decorator

        if len(kw):
            raise TypeError('Unexpected kwargs with `func` parameter')

        return decorator(instcheck(func, Callable))

    @sphinxrole
    @closure
    def role_lexwrite():

        _ctypes = dict(
            valued = {
                LexType.Operator,
                LexType.Quantifier,
                Predicate.System
            }
        )
        _ctypes['nosent'] = _ctypes['valued'] | {
            LexType.Constant,
            LexType.Variable,
            LexType.Predicate,
        }

        def role(self: Helper, /, *, text: str, **_):

            classes = ['lexitem']

            item = None
            match = re.match(r'^(.)([0-9]*)$', text)

            if match:
                char, sub = match.groups()
                table = self.parser.table
                ctype = table.type(char)
                if ctype in _ctypes['nosent']:
                    # Non-sentence items.
                    sub = int(sub) if len(sub) else 0
                    if ctype in _ctypes['valued']:
                        item = table.value(char)
                    elif ctype is LexType.Predicate:
                        preds = self.opts['preds']
                        item = preds.get((table.value(char), sub))
                    else:
                        item = ctype.cls(table.value(char), sub)

            if item is None:
                # Parse as sentence.
                item = self.parser(text)

            classes.append(item.TYPE.name.lower())
            rend = htmlun(self.lwhtml(item))

            return docnodes.inline(text = rend, classes = classes)

        return role

    @sphinxrole
    @closure
    def role_metawrite():

        # langle = '\\langle '
        # rangle = '\\rangle'

        # rdat = dict(
        #     subber = {'P3', 'B3', 'G3', 'K3', 'L3', 'Ł3', 'RM3'},
        #     subsup = {'B3E', 'K3W', 'K3WQ'},
        #     truthvals = {'T', 'F', 'N', 'B'},

        #     # Fixed math strings.
        #     mfixed = {
        #         'ntuple': (f'{langle}a_0,...,a_n{rangle}', ['tuple', 'ntuple'])
        #     },

        #     # Regex sub math.
        #     msubs = tuple((re.compile(p), *a) for p, *a in (
        #         # w0   ->   w_0
        #         (r'^(w)([0-9]+)$', '\\1_\\2', ['modal', 'world']),
        #     )),

        #     # Generic math symbols.
        #     msyms = {
        #         '<': langle,
        #         '>': rangle,
        #     }.items()
        # )
        # # rdat.update((k, re.compile(v)) for k, v in dict(
        # #     # re_prefixed = r'^%s$' % Metawrite['patterns']['prefixed'],
        # #     # re_truthval = r'^V{(%s)}$' % '|'.join(rdat['truthvals']),
        # #     # re_truthval  = r'^V{(.*?)}$',
        # #     # re_logicname = r'^L{(.*?)}$',
        # #     # re_mfixed    = r'^!{(.*?)}$',
        # # ).items())

        # def mathsyms(text: str):
        #     for p, rep in rdat['msyms']:
        #         text = text.replace(p, rep)
        #     return text

        # '\\mathcal{R}'

        def role(self: Helper, /, *, text: str, **_):

            classes = ['metawrite']

            match = re.match(Metawrite['patterns']['prefixed_role'], text)

            if not match:

                # Regex rewrite.
                mode = 'rewrite'
                for pat, info in Metawrite['modes'][mode].items():
                    rend, num = re.subn(pat, info['rep'], text)
                    if num:
                        classes.extend(info['classes'])
                        nodecls = info['nodecls']
                        break
                else:
                    # Generic math symbols.
                    mode = 'math_symbols'
                    nodecls = docnodes.math
                    if 'w' in text:
                        classes.append('modal')
                    if '<' in text and '>' in text:
                        classes.append('tuple')
                    rend = text
                    for pat, rep in Metawrite['generic'][mode].items():
                        rend = re.sub(pat, rep, rend)
                    logger.info((text,rend))

                classes.append(mode)
                return nodecls(text = rend, classes = classes)

            matchd = match.groupdict()
            mode = Metawrite['prefixes'][matchd['prefix']]
            value = matchd['value']
            classes.append(mode)

            moded = Metawrite['modes'][mode]

            if mode == 'fixed':
                try:
                    rend = moded[value]['rend']
                except KeyError:
                    raise ValueError(value)
                classes.extend(moded[value]['classes'])
                return docnodes.math(text = rend, classes = classes)

            if mode == 'truth_value':
                rend = value
                nodecls = moded['nodecls']
                return nodecls(text = rend, classes = classes)

            if mode == 'logic_name':

                for pat, addcls in moded['match'].items():
                    m = re.match(pat, value)
                    if not m:
                        continue
                    md = m.groupdict()
                    classes.extend(addcls)
                    return [
                        nodecls(text = md[key], classes = classes + [key])
                        for key, nodecls in moded['nodecls_map'].items()
                        if key in md
                    ]
                
                rend = value
                return docnodes.inline(text = rend, classes = classes)

            raise NotImplementedError(mode)
        return role

                    # for key, nodcls in {
                    #     'main': docnodes.inline,
                    #     'up'  : docnodes.superscript,
                    #     'down': docnodes.subscript
                    # }.items():
                    #     if key in minfo:


                    # nodes = [
                    #     docnodes.inline(text = m['main'], classes = classes + ['main'])
                    # ]
                    # if 'up' in minfo:
                    #     nodes.append(
                    #         docnodes.superscript(text = up, classes = classes + ['up'])
                    #     )
                    # nodes.append(
                    #     docnodes.subscript(text = down, classes = classes + ['down'])
                    # )

                # if value in rdat['subber']:
                #     classes.append('subber')
                #     main, down = value[0:2]
                #     if len(value) == 3:
                #         main = value[2] + main
                #     if main == 'L':
                #         main = 'Ł'
                #     return [
                #         docnodes.inline(text = main, classes = classes + ['main']),
                #         docnodes.subscript(text = down, classes = classes + ['down']),
                #     ]

                # if value in rdat['subsup']:
                #     classes.append('subsup')
                #     main, up, down = value[0:3]
                #     if len(value) == 4:
                #         down += value[3]
                #     return [
                #         docnodes.inline(text = main, classes = classes + ['main']),
                #         docnodes.superscript(text = up, classes = classes + ['up']),
                #         docnodes.subscript(text = down, classes = classes + ['down']),
                #     ]

            # # Fixed math strings.
            # match = re.match(rdat['re_mfixed'], text)
            # # if text in rdat['mfixed']:
            # if match:
            #     classes.append('mfixed')
            #     key = match.group(1)
            #     try:
            #         rend, addcls = rdat['mfixed'][key]
            #     except KeyError:
            #         raise ValueError(key)
            #     classes.extend(addcls)
            #     return docnodes.math(text = rend, classes = classes)

            # # # Normalization.
            # # if text in rdat['truthvals']:
            # #     logger.info(text)
            # #     text = 'V{%s}' % text
            # # elif text in self.logic_names:
            # #     logger.info(text)
            # #     text = 'L{%s}' % text

            # match = re.match(rdat['re_truthval'], text)
            # if match:
            #     classes.append('truth-value')
            #     rend = match.group(1)
            #     return docnodes.strong(text = rend, classes = classes)

            # # match = re.match(r'^L{(%s)}$' % self.logic_union, text)
            # match = re.match(rdat['re_logicname'], text)
            # if match:
            #     classes.append('logic-name')
            #     logic_name = match.group(1)

            #     if logic_name in rdat['subber']:
            #         classes.append('subber')
            #         main, down = logic_name[0:2]
            #         if len(logic_name) == 3:
            #             main = logic_name[2] + main
            #         if main == 'L':
            #             main = 'Ł'
            #         return [
            #             docnodes.inline(text = main, classes = classes + ['main']),
            #             docnodes.subscript(text = down, classes = classes + ['down']),
            #         ]

            #     if logic_name in rdat['subsup']:
            #         classes.append('subsup')
            #         main, up, down = logic_name[0:3]
            #         if len(logic_name) == 4:
            #             down += logic_name[3]
            #         return [
            #             docnodes.inline(text = main, classes = classes + ['main']),
            #             docnodes.superscript(text = up, classes = classes + ['up']),
            #             docnodes.subscript(text = down, classes = classes + ['down']),
            #         ]

            #     return docnodes.inline(text = logic_name, classes = classes)

            # # Regex sub math.
            # for pat, rep, addcls in rdat['msubs']:
            #     rend, num = re.subn(pat, rep, text)
            #     if num > 0:
            #         classes.extend(addcls)
            #         return docnodes.math(text = rend, classes = classes)

            # # Generic math symbols.
            # if 'w' in text:
            #     classes.append('modal')
            # if '<' in text and '>' in text:
            #     classes.append('tuple')
            # rend = mathsyms(text)

            # # logger.info((text, rend, classes))

            # return docnodes.math(text = rend, classes = classes)

        return role

    ## Doc modifify conditions

    def _should_ruledoc_inherit(self, obj: Any):
        """Whether a rule class:
            - is included in TabRules groups for the module it belongs to
            - inherits from a rule class that belongs to another logic module
            - the parent class is in the other logic's rule goups
            - there is no implementation besides pass
            - there is no docblock
        """
        return (
            isrulecls(obj) and
            isnodoc(obj) and
            isnocode(obj) and
            selfgrouped(obj) and
            parentgrouped(obj)
        )

    def _should_rule_example(self, obj: Any, /, skip = {Rule, ClosingRule}):
        return isrulecls(obj) and obj not in skip

    def _should_trunk_example(self, obj: Any, /, skip = {TabSys.build_trunk}):
        return TabSys.build_trunk in methmro(obj) and obj not in skip

    ## Dispatcher

    def _dispatch_sphinx(self, event: str, args: tuple):
        'Consolidated Sphinx event dispatcher.'
        for func in self._listeners[event]:
            try:
                func(*args)
            except:
                logger.error(
                    f"Event '{event}' failed for "
                    f"{func} with args {args}"
                )
                logger.info('Printing traceback')
                traceback.print_exc()
                raise


def include_directive(app: Sphinx):

    app.add_event('include-read')

    from sphinx.directives.other import Include as BaseInclude

    class Include(BaseInclude):

        def parse(self, text: str, doc):
            lines = text.split('\n')
            source = doc.attributes['source']
            app.emit('include-read', lines)
            self.state_machine.insert_input(lines, source)

        def run(self):
            self.options['parser'] = lambda: self
            super().run()
            return []

    return Include

# Misc util

def rawblock(lines: list[str], indent: str|int = None) -> list[str]:
    'Make a raw html block from the lines. Returns a new list of lines.'
    lines = ['.. raw:: html', '', *indented(lines, 4), '']
    return indented(lines, indent)

def indented(lines: list[str], indent: str|int = None) -> list[str]:
    'Indent non-empty lines. Indent can be string or number of spaces.'
    if indent is None:
        indent = ''
    elif isinstance(indent, int):
        indent *= ' '
    return [
        indent + line if len(line) else line
        for line in lines
    ]

def methmro(meth: Any) -> list[str]:
    """Get the methods of the same name of the mro (safe) of the class the
    method is bound to."""
    try:
        it = (getattr(c, meth.__name__, None) for c in meth.__self__.__mro__)
    except:
        return []
    return list(filter(None, it))

def isnodoc(obj: Any) -> bool:
    return not bool(getattr(obj, '__doc__', None))

def isnocode(obj: Any) -> bool:
    'Try to determine if obj has no "effective" code.'
    isblock = False
    isfirst = True
    pat = re.compile(rf'^(class|def) {obj.__name__}(\([a-zA-Z0-9_.]+\))?:$')
    try:
        it = filter(len, map(str.strip, getsource(obj).split('\n')))
    except:
        return False
    try:
        for line in it:
            if isfirst:
                isfirst = False
                m = re.findall(pat, line)
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
        raise
        return False

def isrulecls(obj: Any) -> bool:
    'Wether obj is a rule class.'
    return isinstance(obj, type) and issubclass(obj, Rule)

def rulegrouped(rule: type[Rule], logic: Any) -> bool:
    'Whether the rule class is grouped in the TabRules of the given logic.'
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

# def set_classes(options: dict):
#     """Set options['classes'] and delete options['class'].

#     From: https://github.com/docutils-mirror/docutils/blob/master/docutils/parsers/rst/roles.py#L385
#     """
#     if 'class' in options:
#         if 'classes' in options:
#             raise KeyError("classes")
#         options['classes'] = options['class']
#         del options['class']

# helper.connect_sphinx(app, 'autodoc-process-signature',
#     'sphinx_filter_signature',
# )
# def sphinx_evtest(self, app, domain, objtype, contentnode):
#     #print('\n\n\n', (domain, objtype, contentnode), '\n')
#     # if pagename == '_modules/logics/fde':
#     #     for n in doctree.traverse():
#     #         print(str(n.attlist()))
#     # # print('\n\n\n', (pagename, templatename), '\n')
#     pass

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