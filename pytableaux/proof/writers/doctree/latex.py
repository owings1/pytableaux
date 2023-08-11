# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
"""
pytableaux.proof.writers.doctree.latex
======================================

"""
from __future__ import annotations


import logging
from collections import deque
from types import MappingProxyType as MapProxy
from typing import Any, Mapping, Sequence

from ....lang import Notation
from ....tools import EMPTY_SET
from ...tableaux import Tableau
from ..jinja import TEMPLATES_BASE_DIR, jinja
from . import DoctreeTabWriter, Translator, nodes, NodeVisitor

class LatexTranslator(Translator, NodeVisitor):
    format = 'latex'
    logger = logging.getLogger(__name__)

class LatexTabWriter(DoctreeTabWriter):

    __slots__ = EMPTY_SET

    format = 'latex'
    translator_type = LatexTranslator

    def build_doc(self, tab: Tableau, /):
        types = self.docnode_type.types
        doc = types[nodes.document]()
        doc += types[nodes.tableau].for_object(tab)
        return doc
