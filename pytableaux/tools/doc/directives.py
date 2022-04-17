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
    'Tableaud',
    'TruthTable',
    'TruthTables',
)

from collections import ChainMap
from docutils import nodes
from docutils.parsers.rst.directives import class_option, unchanged
import re
import sphinx.directives.other
import sphinx.directives.patches
from sphinx.util import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx

import examples
import lexicals
import logics
import models
import parsers
from proof import tableaux, writers
from tools.doc import BaseDirective, SphinxEvent, docparts, rstutils

logger = logging.getLogger(__name__)

# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html


re_space = re.compile(r'\s')
re_comma = re.compile(r',')
divclear_rawhtml = '<div class="clear"></div>'

def cleanws(arg: str, /) -> str:
    "Option spec to remove all whitespace."
    return re_space.sub('', arg)

def predsopt(arg: str, /) -> lexicals.Predicates:
    "Option spec for list of predicate specs."
    return lexicals.Predicates(
        tuple(map(int, spec.split(':')))
        for spec in re_comma.split(cleanws(arg))
    )

def opersopt(arg: str, /) -> tuple[lexicals.Operator, ...]:
    return tuple(map(lexicals.Operator,
        (s.strip() for s in re_comma.split(arg))
    ))

def boolopt(arg: str, /) -> bool:
    if arg:
        arg = arg.strip()
    else:
        arg = 'on'
    arg = arg.lower()
    if arg in ('true', 'yes', 'on'):
        return True
    if arg in ('false', 'no', 'off'):
        return False
    raise ValueError(f"Invalid boolean value: '{arg}'")

class Tableaud(BaseDirective):
    """Tableau directive.
    
    Example::

        .. tableau:: CFOL.Conjunction

        .. tableau::
             :logic: FDE
             :example: Modus Ponens

        .. tableau::
             :logic: FDE
             :conclusion: B
             :premises: A, A > B
    """

    optional_arguments = 1

    option_spec = dict(
        logic = logics.getlogic,
        example = examples.argument,
        conclusion = unchanged,
        premises = re_comma.split,
        pnotn = lexicals.Notation,
        preds = predsopt,
        wnotn = lexicals.Notation,
        classes = class_option,
    )

    opts_with_args = {'wnotn', 'classes'}

    def run(self):

        classes = self.set_classes()
        opts = self.options
        ochain = ChainMap(opts, self.helper.opts)

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
                if 'example' in opts:
                    arg = opts['example']
                    if 'conclusion' in opts:
                        raise self.error(f"'conclusion' not allowed with 'example'")
                else:
                    arg = parser.argument(opts['conclusion'], opts.get('premises'))
                tab = tableaux.Tableau(opts['logic'], arg)
            except KeyError as e:
                raise self.error(f'Missing required option: {e}')

        pw = writers.TabWriter('html', ochain['wnotn'], classes = classes)
        return [nodes.raw(format = 'html', text = pw(tab.build()))]

class TruthTable(BaseDirective):
    'Truth table (raw html).'

    #: <Logic>.<Operator>
    required_arguments = 1

    option_spec = dict(
        wnotn = lexicals.Notation,
        template = unchanged,
        reverse = boolopt,
        clear = boolopt,
        classes = class_option,
    )

    def run(self):

        classes = self.set_classes()
        opts = self.options
        helper = self.helper
        hopts = helper.opts
        ochain = ChainMap(opts, hopts)

        argstr, = self.arguments
        try:
            logic, oper = argstr.split('.')
            logic = logics.getlogic(logic)
            model: models.BaseModel = logic.Model()
            oper = lexicals.Operator(oper)
        except Exception as e:
            logger.error(e)
            raise self.error(f'Bad operator argument: {argstr}')

        lw = lexicals.LexWriter(ochain['wnotn'], 'html')

        template = opts.get('template', hopts['truth_table_template'])
        reverse = opts.get('reverse', hopts['truth_table_reverse'])
        clear = opts.get('clear', True)

        table = model.truth_table(oper, reverse = reverse)
        context = dict(table = table, lw = lw, classes = classes)
        content = helper.render(template, context)
        if clear:
            content += divclear_rawhtml

        return [nodes.raw(format = 'html', text = content)]

class TruthTables(BaseDirective):
    'Truth tables (raw html) of all operators.'

    #: Logic
    required_arguments = 1

    option_spec = dict(
        operators = opersopt,
        wnotn = lexicals.Notation,
        template = unchanged,
        reverse = boolopt,
        clear = boolopt,
        classes = class_option,
    )

    def run(self):

        classes = self.set_classes()
        helper = self.helper
        opts = helper.opts
        hopts = helper.opts
        ochain = ChainMap(opts, hopts)

        logic = logics.getlogic(self.arguments[0])
        model: models.BaseModel = logic.Model()
        opers = opts.get('operators')
        if opers is None:
            opers = sorted(model.truth_functional_operators)

        lw = lexicals.LexWriter(ochain['wnotn'], 'html')

        template = opts.get('template', hopts['truth_table_template'])
        reverse = opts.get('reverse', hopts['truth_table_reverse'])
        clear = opts.get('clear', True)

        tables = (
            model.truth_table(oper, reverse = reverse)
            for oper in opers
        )
        context = dict(lw = lw, classes = classes)
        renders = (
            helper.render(template, context, table = table)
            for table in tables
        )
        content = '\n'.join(renders)
        if clear:
            content += divclear_rawhtml

        return [nodes.raw(format = 'html', text = content)]

class CSVTable(sphinx.directives.patches.CSVTable, BaseDirective):
    "Override csv-table to allow generator function."

    generators = dict(
        opers_table = docparts.opers_table
    )

    def generator_opt(arg: str):
        try:
            return CSVTable.generators[arg]
        except KeyError:
            raise ValueError(f"Invalid CSVTable generator name: '{arg}'")

    option_spec = dict(sphinx.directives.patches.CSVTable.option_spec,
        generator = generator_opt,
    )

    def get_csv_data(self):
        # Override docutils.parsers.rst.directives.CSVTable.get_csv_data()
        generator = self.options.get('generator')
        if generator is None:
            return super().get_csv_data()
        rows = generator()
        source = '_generator'
        return rstutils.csvlines(rows), source

class Include(sphinx.directives.other.Include, BaseDirective):
    "Override include directive that allows the app to modify content via events."

    def parse(self, text: str, doc):
        lines = text.splitlines()
        source = doc.attributes['source']
        self.env.app.emit(SphinxEvent.IncludeRead, lines)
        self.state_machine.insert_input(lines, source)

    def run(self):
        self.options['parser'] = self.faux_parser
        super().run()
        return []

    def faux_parser(self):
        return self

def setup(app: Sphinx):
    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('tableau', Tableaud)
    app.add_directive('truth-table', TruthTable)
    app.add_directive('truth-tables', TruthTables)
    