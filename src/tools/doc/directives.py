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
# pytableaux - directives module
from __future__ import annotations
from typing import Any

from models import BaseModel
from tools.misc import get_logic

__all__ = (
    'CSVTable',
    'Include',
    'Inject'
    # 'include_directive',
)

from docutils import nodes
import docutils.parsers.rst.directives.tables as _tables
from docutils.parsers.rst.directives import unchanged
from sphinx.application import Sphinx
import sphinx.directives
import sphinx.directives.other
from sphinx.util import logging
from tools.doc import SphinxEvent
from tools.doc.extension import gethelper
from tools.doc import docparts, rstutils

logger = logging.getLogger(__name__)

class BaseDirective(sphinx.directives.SphinxDirective):
    @property
    def helper(self):
        return gethelper(self.env.app)

class Inject(BaseDirective):

    required_arguments = 1
    optional_arguments = 1
    has_content = True

    def run(self):
        classes = []
        info = dict(
            arguments = self.arguments,
            content   = self.content,
            options   = self.options,
            block_text = self.block_text,
        )

        # logger.info(info)
        cmd, *args = self.arguments
        meth = getattr(self, f'cmd_{cmd}', None)
        if meth is None:
            raise self.error(f"Invalid command: '{cmd}'")
        self.cmdargs = args
        ret = meth(*args)
        if isinstance(ret, list):
            return ret
        return [ret]

    # def cmd_truth_tables(self, logic: str):
    #     lines = self.helper.lines_truth_tables(logic)
    #     return nodes.raw(text='\n'.join(lines), format = 'html')

    def cmd_truth_tables(self, logic: str):
        'Truth tables (raw html) of all operators.'
        m: BaseModel = get_logic(logic).Model()
        helper = self.helper
        opts = helper.opts
        template = opts['truth_table_tmpl']
        reverse = opts['truth_tables_rev']
        tables = (
            m.truth_table(oper, reverse = reverse)
            for oper in m.truth_functional_operators
        )
        renders = (
            helper.render(template, table = table, lw = helper.lwhtml)
            for table in tables
        )
        content = '\n'.join(renders) + '<div class="clear"></div>'
        return nodes.raw(text = content, format = 'html')

class CSVTable(_tables.CSVTable, BaseDirective):
    
    option_spec = _tables.CSVTable.option_spec | dict(
        generator = unchanged,
    )
    generators = dict(
        opers_table = docparts.opers_table
    )
    def get_csv_data(self):
        genname = self.options.get('generator')
        if not genname:
            return super().get_csv_data()
        generator = self.generators.get(genname)
        if generator is None:
            raise self.error(f"Invalid table generator name: '{genname}'")
        rows = generator()
        return rstutils.csvlines(rows), '_generator'

class Include(sphinx.directives.other.Include, BaseDirective):
    "Override include directive that allows the app to modify content via events."

    def parse(self, text: str, doc):
        lines = text.split('\n')
        source = doc.attributes['source']
        self.env.app.emit(SphinxEvent.IncludeRead, lines)
        self.state_machine.insert_input(lines, source)

    def run(self):
        self.options['parser'] = lambda: self
        super().run()
        return []

