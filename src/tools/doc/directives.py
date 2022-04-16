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

__all__ = (
    'CSVTable',
    'Include',
    'Inject',
    'Tableaud',
    'TruthTable',
)

from collections import ChainMap
from docutils import nodes
from docutils.parsers.rst.directives import class_option, flag, unchanged
import re
from sphinx import directives
from sphinx.util import logging
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sphinx.application import Sphinx


from tools.doc import SphinxEvent
from tools.doc import BaseDirective, docparts, rstutils

import lexicals
import logics
import models
import parsers
from proof import tableaux, writers

logger = logging.getLogger(__name__)

# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html



_re_ws = re.compile(r'\s')

def cleanws(arg):
    return _re_ws.sub('', arg)

class Tableaud(BaseDirective):
    """Tableau directive.
    
    Example::

        .. tableau:: CFOL.Conjunction

        .. tableau::
             :logic: FDE
             :conclusion: B
             :premises: A, A > B
    """

    def predsopt(arg: str):
        return lexicals.Predicates(
            tuple(map(int, spec.split(':')))
            for spec in cleanws(arg).split(',')
        )

    optional_arguments = 1
    option_spec = dict(
        logic = logics.getlogic,
        conclusion = unchanged,
        premises = re.compile(r',').split,
        pnotn = lexicals.Notation,
        preds = predsopt,
        wnotn = lexicals.Notation,
        classes = class_option,
    )

    opts_with_args = {'wnotn', 'classes'}

    def run(self):

        opts = self.options
        ochain = ChainMap(opts, self.helper.opts)
        classes = self.set_classes()

        if len(self.arguments):
            badopts = set(opts) - self.opts_with_args
            if badopts:
                raise self.error(
                    f'Option not allowed with arguments: {badopts}')

            rulestr, = self.arguments
            try:
                logic, rulename = rulestr.split('.')
                logic = logics.getlogic(logic)
                rule = getattr(logic.TabRules, rulename)
            except Exception as e:
                logger.error(e)
                raise self.error(f'Bad rule argument: {rulestr}')

            classes.extend(('example', 'rule'))
            if issubclass(rule, tableaux.ClosingRule):
                classes.append('closure')
            tab = docparts.rule_example_tableau(rule)

        else:
            parser = parsers.Parser(ochain['pnotn'], ochain['preds'])
            try:
                arg = parser.argument(opts['conclusion'], opts.get('premises'))
                tab = tableaux.Tableau(opts['logic'], arg)
            except KeyError as e:
                raise self.error(f'Missing required option: {e}')

        pw = writers.TabWriter('html', ochain['wnotn'], classes = classes)
        return [nodes.raw(format = 'html', text = pw(tab.build()))]

class TruthTable(BaseDirective):
    required_arguments = 1
    option_spec = dict(
        template = unchanged,
        noreverse = flag,
        noclear = flag,
        classes = class_option,
    )
    def run(self):
        classes = self.set_classes()
        opts = self.options
        helper = self.helper
        hopts = helper.opts
        argstr, = self.arguments
        try:
            logic, oper = argstr.split('.')
            logic = logics.getlogic(logic)
            oper = lexicals.Operator(oper)
        except Exception as e:
            logger.error(e)
            raise self.error(f'Bad operator argument: {argstr}')
        template = opts.get('template', hopts['truth_table_tmpl'])
        noreverse = 'noreverse' in opts or not hopts['truth_tables_rev']
        noclear = 'noclear' in opts
        m: models.BaseModel = logic.Model()
        table = m.truth_table(oper, reverse = not noreverse)
        content = helper.render(template,
            table = table, lw = helper.lwhtml, classes = classes
        )
        if not noclear:
            content += '<div class="clear"></div>'
        return [nodes.raw(text = content, format = 'html')]

class Inject(BaseDirective):

    required_arguments = 1
    optional_arguments = 1
    has_content = True
    option_spec = dict(
        classes = class_option
        
    )
    def run(self):
        self.set_classes()
        cmd, *args = self.arguments
        meth = getattr(self, f'cmd_{cmd}', None)
        if meth is None:
            raise self.error(f"Invalid command: '{cmd}'")
        self.cmdargs = args
        ret = meth(*args)
        if isinstance(ret, list):
            return ret
        return [ret]

    def cmd_truth_tables(self, logic: str):
        'Truth tables (raw html) of all operators.'
        m: models.BaseModel = logics.getlogic(logic).Model()
        helper = self.helper
        opts = helper.opts
        template = opts['truth_table_tmpl']
        reverse = opts['truth_tables_rev']
        tables = (
            m.truth_table(oper, reverse = reverse)
            for oper in sorted(m.truth_functional_operators)
        )
        renders = (
            helper.render(template, table = table, lw = helper.lwhtml)
            for table in tables
        )
        content = '\n'.join(renders) + '<div class="clear"></div>'
        return nodes.raw(text = content, format = 'html')

class CSVTable(directives.patches.CSVTable, BaseDirective):
    generators = dict(
        opers_table = docparts.opers_table
    )
    def genopt(arg, /, *, base = generators):
        if arg in base:
            return arg
        raise ValueError(f"Invalid table generator name: '{arg}'")

    option_spec = dict(directives.patches.CSVTable.option_spec,
        generator = genopt,
    )

    def get_csv_data(self):
        genname = self.options.get('generator')
        if not genname:
            return super().get_csv_data()
        rows = self.generators[genname]()
        return rstutils.csvlines(rows), '_generator'

class Include(directives.other.Include, BaseDirective):
    "Override include directive that allows the app to modify content via events."

    def parser(self):
        return self

    def parse(self, text: str, doc):
        lines = text.split('\n')
        source = doc.attributes['source']
        self.env.app.emit(SphinxEvent.IncludeRead, lines)
        self.state_machine.insert_input(lines, source)

    def run(self):
        self.options['parser'] = self.parser
        super().run()
        return []


del(directives)


def setup(app: Sphinx):
    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('inject',  Inject)  
    app.add_directive('tableau', Tableaud)
    app.add_directive('truth-table', TruthTable)
    
