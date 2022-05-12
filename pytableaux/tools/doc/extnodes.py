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
"""
pytableaux.tools.doc.extnodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes

import itertools
if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = (
    'sentence',
    'block',
)

class sentence(nodes.inline, nodes.TextElement): pass
class block(nodes.Element): pass

def visit_block_html(self, node):
    self.body.append(self.starttag(node, 'div', ''))

def depart_block_html(self, node):
    self.body.append('</div>\n')

def _noop(self, node): pass
def _skip(self, node):
    raise nodes.SkipNode

def setup(app: Sphinx):

    app.add_node(sentence)

    names = app.registry.translators.keys()
    noops = dict(zip(names, itertools.repeat(_noop)))

    app.add_node(block, **dict(noops,
        html = (visit_block_html, depart_block_html),
    ))
