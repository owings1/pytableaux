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

from typing import TYPE_CHECKING

from pytableaux.tools import abcs

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


class ConfKey(str, abcs.Ebc):
    'Custom config keys.'

    copy_file_tree = 'copy_file_tree'
    "The config key for file tree copy actions."

    auto_skip_enum_value = 'autodoc_skip_enum_value'

    wnotn = 'lex_write_notation'
    pnotn = 'lex_parse_notation'
    preds = 'lex_parse_predicates'

    truth_table_template = 'truth_table_template'
    truth_table_reverse = 'truth_table_reverse'

    templates_path = 'templates_path'



def setup(app: Sphinx):
    'Setup the Sphinx application.'

    from pytableaux.tools import doc
    from pytableaux.tools.doc import directives, processors, roles, tables

    doc.setup(app)

    directives.setup(app)
    tables.setup(app)
    processors.setup(app)
    roles.setup(app)




