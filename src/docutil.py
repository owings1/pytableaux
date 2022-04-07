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
from tools._docext import include_directive, LexwriteRole, MetawriteRole
from tools import _docinspect
from tools.abcs import F, MapProxy
from tools.decorators import closure, overload, wraps
from tools.misc import get_logic

from collections import defaultdict
from docutils import nodes as docnodes
from html import unescape as htmlun
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

logger = logging.getLogger(__name__)

class Helper:

    _defaults = MapProxy(dict(
        template_dir     = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../doc/templates')
        ),
        truth_table_tmpl = 'truth_table.jinja2',
        truth_tables_rev = True,
        write_notation   = Notation.standard,
        parse_notation   = Notation.standard,
        preds            = examples.preds,
        lexwrite_roles   = ('s',),
        metawrite_roles  = ('m',),
        new_include      = True,
    ))

    @staticmethod
    def setup_sphinx(app: Sphinx, **opts) -> Helper:

        helper = Helper(**opts)
        opts = helper.opts

        helper.connect_sphinx(app, 'autodoc-process-docstring',
            helper.sphinx_obj_lines_append_autodoc,
            helper.sphinx_line_replace_autodoc,
            helper.sphinx_simple_replace_autodoc,
        )

        helper.connect_sphinx(app, 'source-read',
            helper.sphinx_line_replace_source,
            helper.sphinx_simple_replace_source,
        )

        if opts['new_include']:
            Include = include_directive(app)
            app.add_directive('include', Include, override = True)

            helper.connect_sphinx(app, 'include-read',
                helper.sphinx_line_replace_include,
                helper.sphinx_simple_replace_include,
            )

        if opts['lexwrite_roles']:
            instcheck(opts['lexwrite_roles'], tuple)
            inst = LexwriteRole(**opts)
            for name in opts['lexwrite_roles']:
                app.add_role(name, inst)

        if opts['metawrite_roles']:
            instcheck(opts['metawrite_roles'], tuple)
            inst = MetawriteRole()
            app.add_role('moo', inst)
            for name in opts['metawrite_roles']:
                app.add_role(name, inst)

        return helper

    DIV_CLEAR = '<div class="clear"></div>'

    logic_union = '|'.join(
        sorted(_docinspect.get_logic_names(), key = len, reverse = True)
    )

    def __init__(self, **opts):

        from proof.writers import TabWriter
        import jinja2

        self.opts = opts = dict(self._defaults) | opts

        instcheck(opts['lexwrite_roles'], tuple)
        instcheck(opts['metawrite_roles'], tuple)

        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(opts['template_dir']),
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

    def lines_rule_example(self, rule: Rule|type[Rule], /, logic: Any = None, indent: str|int = None):
        'ReST lines for ``Rule`` example.'
        tab = _docinspect.rule_example_tableau(rule, logic)
        rule = tab.rules.get(rule)
        if isinstance(rule, ClosingRule):
            pw = self.pwclosure
        else:
            pw = self.pwrule
        lines = ['Example:', '']
        lines.extend(rawblock(pw(tab).split('\n')))
        return indented(lines, indent)

    def lines_trunk_example(self, logic: Any, indent: str|int = None) -> list[str]:
        'ReST lines for ``build_trunk`` example.'
        arg = Parser('polish').argument('b', ('a1', 'a2'))
        tab = _docinspect.trunk_example_tableau(logic, arg)
        pw = self.pwtrunk
        lw = pw.lw
        if lw.charset != 'html':
            raise TypeError(f'Incompatible charset {repr(lw.charset)}')
        lines = ['Example:', '']
        # Render argument.
        pstr = '</i> ... <i>'.join(map(lw, arg.premises))
        argstr = f'Argument: <i>{pstr}</i> &there4; <i>{lw(arg.conclusion)}</i>'
        lines = argstr.split('\n')
        lines.extend(pw(tab).split('\n'))
        return indented(rawblock(lines), indent)

    def lines_truth_tables(self, logic: Any, indent: str|int = None) -> list[str]:
        'ReST lines for truth tables of all operators.'
        m: BaseModel = get_logic(logic).Model()
        opts = self.opts
        render = self.jenv.get_template(opts['truth_table_tmpl']).render
        reverse = opts['truth_tables_rev']
        lines = [
            line
            for oper in sorted(m.truth_functional_operators)
                for line in render(
                    table = m.truth_table(oper, reverse = reverse),
                    lw = self.lwhtml
                ).split('\n')
        ]
        lines.append(self.DIV_CLEAR)
        return rawblock(lines, indent)

    def lines_ruledoc_inherit(self, rule: type[Rule], indent: str|int = None):
        'ReST docstring lines for an "inheriting only" ``Rule`` class.'
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


    _simple_replace = None
    _line_replace   = None

    @closure
    def _simple_replace_common(logic_union = logic_union):

        def logic_ref(match: re.Match):
            # Link to a logic:
            #   {@K3}        -> :ref:`K3 <K3>`
            #   {@FDE Model} -> :ref:`FDE Model <fde-model>`
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
                    slug = '-'.join(re.split(r'\s+', title.lower()))
                anchor = f'<{slug}>'
            return f":ref:`{title} {anchor}`"

        logic_ref_pat = (
            r'{@(?P<name>%s)' % logic_union +
            r'(?:\s+(?P<sect>[\sa-zA-Z-]+)?(?P<anchor><.*?>)?)?}'
        )

        def getdefns(self: Helper):
            defns = self._simple_replace
            if defns is not None:
                return defns

            opts = self.opts

            # regex: rolename
            rolemap = {
                MetawriteRole.patterns['prefixed']: opts['metawrite_roles'][0]
            }
            defns = tuple(
                (r'(?<!`)' + pat, f':{name}:`\\1`')
                for pat, name in rolemap.items()
            ) + (
                (logic_ref_pat, logic_ref),
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

    @closure
    def sphinx_obj_lines_append_autodoc():

        from tools._docinspect import (
            is_concrete_rule,
            is_concrete_build_trunk,
            is_transparent_rule,
        )

        def run(self: Helper, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]):
            """Append lines to a docstring extracted from the autodoc extention.
            For injecting into doc source files, use a regex line replacement.
            """
            defns = (
                (is_transparent_rule,     self.lines_ruledoc_inherit),
                (is_concrete_rule,        self.lines_rule_example),
                (is_concrete_build_trunk, self.lines_trunk_example),
            )
            for check, func in defns:
                if check(obj):
                    lines.extend(func(obj))

        return run


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
