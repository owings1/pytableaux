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
# pytableaux - sphinx extension
from __future__ import annotations
import os
import shutil

from typing import TYPE_CHECKING, Mapping, Optional
import sphinx.config
from pytableaux.errors import check
from pytableaux.lang import Notation, Predicates
from pytableaux.tools import MapProxy, abcs, closure

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = (
    'ConfKey',
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
# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html



# helpers: Mapping[Sphinx, Helper] = None
# "The Shinx application ``Helper`` instances."


class ConfKey(str, abcs.Ebc):
    'Custom config keys.'

    options = 'pt_options'
    "The config key for helper options."

    htmlcopy = 'pt_htmlcopy'
    "The config key for html copy actions."

    auto_skip_enum_value = 'autodoc_skip_enum_value'

    wnotn = 'lex_write_notation'
    pnotn = 'lex_parse_notation'
    preds = 'lex_parse_predicates'

    truth_table_template = 'truth_table_template'
    truth_table_reverse = 'truth_table_reverse'

    templates_path = 'templates_path'
    jenv = '_app_jenv'

# class Helper(abcs.Abc):

#     __slots__ = (
#         'jenv',
#         'opts',
#         'pwtrunk',
#     )

#     defaults = dict(
#         wnotn = 'standard',
#         pnotn = 'standard',
#         preds = ((0,0,1), (1,0,1), (2,0,1)),
#         truth_table_template = 'truth_table.jinja2',
#         truth_table_reverse = True,
#         templates_path = (),
#     )

#     def __init__(self, **opts):
#         self.reconfigure(opts)

#     def reconfigure(self, opts: dict):

#         self.opts = opts = dict(self.defaults) | opts

#         self.jenv = jinja2.Environment(
#             loader = jinja2.FileSystemLoader(opts['templates_path']),
#             trim_blocks = True,
#             lstrip_blocks = True,
#         )

#         # opts['preds'] = Predicates(opts['preds'])

#         # wnotn = Notation(opts['wnotn'])

#         # # Make a RenderSet that renders subscript 2 as 'n'.
#         # rskey = f'{type(self).__qualname__}.trunk'
#         # try:
#         #     rstrunk = RenderSet.fetch(wnotn, rskey)
#         # except KeyError:
#         #     rshtml = RenderSet.fetch(wnotn, 'html')
#         #     rstrunk = RenderSet.load(wnotn, rskey, dict(rshtml.data,
#         #         name = f'{wnotn.name}.{rskey}',
#         #         renders = dict(rshtml.renders,
#         #             subscript = lambda sub: (
#         #                 '<sub>%s</sub>' % ('n' if sub == 2 else sub)
#         #             )
#         #         )
#         #     ))

#         # self.pwtrunk = writers.TabWriter('html',
#         #     lw = LexWriter(wnotn, renderset = rstrunk),
#         #     classes = ('example', 'build-trunk'),
#         # )

#     def render(self, template: str, *args, **kw) -> str:
#         "Render a jinja2 template from the template path."
#         return self.jenv.get_template(template).render(*args, **kw)

def htmlcopy_validate(app: Sphinx, config: sphinx.config.Config):

    for entry in config[ConfKey.htmlcopy]:
        check.inst(entry, (list, tuple))
        src, dest = entry[0:2]
        eopts = entry[2] if len(entry) > 2 else {}
        check.inst(src, str)
        check.inst(dest, str)
        check.inst(eopts, dict)

def htmlcopy_run(app: Sphinx, e: Exception|None):

    if app.builder.format != 'html':
        return

    for entry in app.config[ConfKey.htmlcopy]:

        src = os.path.join(app.srcdir, entry[0])
        dest = os.path.join(app.outdir, entry[1])
        eopts = dict(entry[2]) if len(entry) > 2 else {}
        eopts.setdefault('dirs_exist_ok', True)
        ignore = eopts.get('ignore')
        if ignore is not None:
            if not callable(ignore):
                if isinstance(ignore, str):
                    ignore = ignore,
                eopts['ignore'] = shutil.ignore_patterns(*ignore)
        shutil.copytree(src, dest, **eopts)

# @closure
# def setup():

    # global helpers

    # _helpers: dict[Sphinx, Helper]  = {}
    # helpers = MapProxy(_helpers)





        # del _helpers[app]

    # def validate_copy_entry(entry: _HtmlCopyEntry):



    # def do_copy_entry(app: Sphinx, entry: _HtmlCopyEntry):



def setup(app: Sphinx):
    'Setup the Sphinx application.'


    app.add_config_value(ConfKey.wnotn, 'standard', 'env', [str, Notation])
    app.add_config_value(ConfKey.pnotn, 'standard', 'env', [str, Notation])
    app.add_config_value(ConfKey.preds, ((0,0,1), (1,0,1), (2,0,1)), 'env', [tuple, Predicates])

    # app.add_config_value(ConfKey.options, {}, 'env', [dict])
    app.add_config_value(ConfKey.htmlcopy, [], 'env', [list[_HtmlCopyEntry]])

    from pytableaux.tools.doc import (directives, docparts, processors,
                                        roles, setup)
    setup(app)
    directives.setup(app)
    docparts.setup(app)
    processors.setup(app)
    roles.setup(app)

    app.connect('config-inited', htmlcopy_validate)
    app.connect('build-finished', htmlcopy_run)

    # return setup




        # if app in helpers:
        #     raise ValueError(f"app already initialized.")


    #     opts = dict(config[ConfKey.options])

    #     # Add app templates_path to search path.
    #     opts['templates_path'] = [
    #         os.path.join(app.srcdir, tp)
    #         for tp in itertools.chain(
    #             opts.get('templates_path', ()),
    #             config[ConfKey.templates_path],
    #         )
    #     ]
    #     jenv = jinja2.Environment(
    #         loader = jinja2.FileSystemLoader(opts['templates_path']),
    #         trim_blocks = True,
    #         lstrip_blocks = True,
    #     )
    #     _helpers[app] = Helper(**opts)

_HtmlCopyEntry = tuple[str, str, Optional[dict]]
