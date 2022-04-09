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

from lexicals import (
    LexWriter,
    Notation,
    RenderSet,
)

from tools import closure
from tools.doc import roles

import os
import re
from sphinx.application import Sphinx
from sphinx.util import logging
from typing import Any

logger = logging.getLogger(__name__)

class Helper:

    _defaults = dict(
        template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../doc/templates')
        ),
        truth_table_tmpl = 'truth_table.jinja2',
        truth_tables_rev = True,
        wnotn = 'standard',
    )

    def __init__(self, **opts):
        self.reconfigure(opts)

    def reconfigure(self, opts: dict):

        from proof.writers import TabWriter
        import jinja2

        self.opts = opts = dict(self._defaults) | opts

        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(opts['template_dir']),
            trim_blocks = True,
            lstrip_blocks = True,
        )

        wnotn = Notation(opts['wnotn'])
        self.lwhtml = LexWriter(wnotn, 'html')

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
            rstrunk = RenderSet.fetch(wnotn, rskey)
        except KeyError:
            rshtml = RenderSet.fetch(wnotn, 'html')
            rstrunk = RenderSet.load(wnotn, rskey, dict(rshtml.data,
                name = f'{wnotn.name}.{rskey}',
                renders = dict(rshtml.renders,
                    subscript = lambda sub: (
                        '<sub>%s</sub>' % ('n' if sub == 2 else sub)
                    )
                )
            ))

        self.pwtrunk = TabWriter('html',
            lw = LexWriter(wnotn, renderset = rstrunk),
            classes = ('example', 'build-trunk'),
        )
        self._simple_replace = None
        self._line_replace   = None

    def render(self, template: str, *args, **kw) -> str:
        return self.jenv.get_template(template).render(*args, **kw)

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

    @closure
    def _simple_replace_common():

        def getdefns(self: Helper):
            defns = self._simple_replace
            if defns is not None:
                return defns

            rolewrap = {
                roles.metadress: ['prefixed'],
                roles.refplus  : ['logicref'],
            }
            defns = []
            for rolecls, patnames in rolewrap.items():
                entry = roles.getentry(rolecls)
                if entry is not None:
                    rep = f':{entry.name}:'r'`\1`'
                    for patname in patnames:
                        pat = rolecls.patterns[patname]
                        pat = re.compile(r'(?<!`)' + rolecls.patterns[patname])
                        defns.append((pat, rep))

            self._simple_replace = defns
            return defns

        def common(self: Helper, lines: list[str], mode: str = None):
            defns = getdefns(self)
            text = '\n'.join(lines)
            count = 0
            for pat, rep in defns:
                text, num = pat.subn(rep, text)
                count += num
            if count:
                if mode == 'source':
                    lines[0]= text
                else:
                    lines.clear()
                    lines.extend(text.split('\n'))

        return common


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
