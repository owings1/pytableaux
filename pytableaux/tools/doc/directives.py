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
"""
pytableaux.tools.doc.directives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from __future__ import annotations

from collections import ChainMap
from typing import TYPE_CHECKING

import sphinx.directives.other
import sphinx.directives.patches
from docutils import nodes
from pytableaux import examples, logics, models, tools
from pytableaux.lang import Argument, Notation
from pytableaux.lang.lex import Operator
from pytableaux.lang.parsing import Parser
from pytableaux.lang.writing import LexWriter
from pytableaux.proof import rules, tableaux, writers
from pytableaux.proof.helpers import EllipsisExampleHelper
from pytableaux.tools.doc import (BaseDirective, DirectiveHelper, SphinxEvent,
                                  boolopt, choiceopt, classopt, opersopt,
                                  predsopt, re_comma, rstutils, stropt)
from pytableaux.tools.doc.extension import ConfKey
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any

    import sphinx.config
    from pytableaux.tools.doc.docparts import Tabler
    from sphinx.application import Sphinx

__all__ = (
    'CSVTable',
    'Include',
    'Tableaud',
    'TruthTable',
    'TruthTables',
)

logger = logging.getLogger(__name__)

# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html


class TableGenerator(DirectiveHelper):
    'Table generator directive helper.'

    @tools.abstract
    def gentable(self) -> Tabler: ...

    def run(self):
        table = self.gentable()
        opts = self.options
        opts.setdefault('header-rows', len(table.header))
        return table

table_generators: dict[str, TableGenerator] = {}
"Table generator registry."


class Tableaud(BaseDirective):
    """Tableau directive.
    
    For rule example::

        .. tableau::
            :logic: CFOL
            :rule: Conjunction

    For an argument::

        .. tableau::
             :logic: FDE
             :conclusion: B
             :premises: A, A > B

        .. tableau::
             :logic: FDE
             :argument: Modus Ponens
    """

    optional_arguments = 1

    option_spec = dict(
        logic = logics.registry,

        argument = examples.argument,
        conclusion = stropt,
        premises = re_comma.split,
        pnotn = Notation,
        preds = predsopt,

        rule = stropt,

        format = choiceopt(writers.registry),
        wnotn = Notation,

        classes = classopt,
    )

    opts_for_argument = {'argument', 'conclusion', 'premises', 'pnotn', 'preds'}

    def run(self):

        opts = self.options
        opts['classes'] = classes = self.set_classes()

        if 'rule' in opts:
            if (badopts := self.opts_for_argument & set(opts)):
                raise self.error(f"Option not allows with 'rule': {badopts}")
            tab = self.gettab_rule()
        else:
            tab = self.gettab_argument()

        tab.build()

        wnotn = opts.get('wnotn', self.config[ConfKey.wnotn])
        wfmt = opts.get('format', 'html')
        writer = writers.TabWriter(wfmt, wnotn, classes = classes)

        output = writer(tab)

        if wfmt == 'html':
            return [nodes.raw(format = 'html', text = output)]
        else:
            classes |= 'tableau',
            return [nodes.literal_block(text = output, classes = classes)]

    def gettab_rule(self):

        opts = self.options
        classes = opts['classes']
        classes |= ['rule', 'example']

        try:
            tab = tableaux.Tableau(opts['logic'])
            ref: str = opts['rule']
            rule = tab.rules.get(ref)
            
        except KeyError as e:
            raise self.error(f'Missing required option: {e}')
        except AttributeError as e:
            logger.error(e)
            raise self.error(f'Bad rule: {e}')

        if isinstance(rule, rules.ClosingRule):
            classes |= ['closure']
        else:
            rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)

        tab.branch().extend(rule.example_nodes())

        # rule.apply(rule.target(b))
        return tab

    def gettab_argument(self):

        opts = self.options
        arg: Argument
        try:
            logic = opts['logic']
            if 'argument' in opts:
                if (badopts := ({'conclusion', 'premises'} & set(opts))):
                    raise self.error(f"Option not allows with 'argument': {badopts}")
                arg = opts['argument']
            else:
                ochain = ChainMap(opts, self.helper.opts)
                parser = Parser(ochain['pnotn'], ochain['preds'])
                arg = parser.argument(opts['conclusion'], opts.get('premises'))
        except KeyError as e:
            raise self.error(f'Missing required option: {e}')

        return tableaux.Tableau(logic, arg)

class TruthTable(BaseDirective):
    'Truth table (raw html).'

    #: <Logic>.<Operator>
    required_arguments = 1

    option_spec = dict(
        wnotn = Notation,
        template = stropt,
        reverse = boolopt,
        clear = boolopt,
        classes = classopt,
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
            logic = logics.registry(logic)
            model: models.BaseModel = logic.Model()
            oper = Operator(oper)
        except Exception as e:
            logger.error(e)
            raise self.error(f'Bad operator argument: {argstr}')

        lw = LexWriter(ochain['wnotn'], 'html')

        template = opts.get('template', hopts['truth_table_template'])
        reverse = opts.get('reverse', hopts['truth_table_reverse'])
        clear = opts.get('clear', True)

        table = model.truth_table(oper, reverse = reverse)
        context = dict(table = table, lw = lw, classes = classes)
        content = helper.render(template, context)
        if clear:
            content += '<div class="clear"></div>'

        return [nodes.raw(format = 'html', text = content)]

class TruthTables(BaseDirective):
    'Truth tables (raw html) of all operators.'

    #: Logic
    required_arguments = 1

    option_spec = dict(
        operators = opersopt,
        wnotn = Notation,
        template = stropt,
        reverse = boolopt,
        clear = boolopt,
        classes = classopt,
    )

    def run(self):

        classes = self.set_classes()
        # helper = self.helper
        # opts = helper.opts
        # hopts = helper.opts
        # ochain = ChainMap(opts, hopts)
        opts = self.options
        logic = logics.registry(self.arguments[0])
        model: models.BaseModel = logic.Model()
        opers = opts.get('operators')
        if opers is None:
            opers = sorted(model.truth_functional_operators)

        wnotn = opts.get('wnotn', self.config[ConfKey.wnotn])
        lw = LexWriter(wnotn, 'html')

        template = opts.get('template', self.config[ConfKey.truth_table_template])
        reverse = opts.get('reverse', self.config[ConfKey.truth_table_reverse])
        clear = opts.get('clear', True)

        tables = (
            model.truth_table(oper, reverse = reverse)
            for oper in opers
        )
        context = dict(lw = lw, classes = classes)
        renders = (
            self.render(template, context, table = table)
            for table in tables
        )
        content = '\n'.join(renders)
        if clear:
            content += '<div class="clear"></div>'

        return [nodes.raw(format = 'html', text = content)]

    def render(self, template, *args, **kw):
        return self.jenv.get_template(template).render(*args, **kw)

class CSVTable(sphinx.directives.patches.CSVTable, BaseDirective):
    "Override csv-table to allow generator function."

    generator: TableGenerator|None
    option_spec = dict(sphinx.directives.patches.CSVTable.option_spec) | {
        'generator'      : table_generators.__getitem__,
        'generator-args' : stropt,
        'classes'        : classopt,
    }

    option_spec.pop('class', None)

    def run(self):

        classes = self.set_classes()
        opts = self.options

        if (GenCls := opts.get('generator')) is None:
            self.generator = None
        else:
            self.generator = GenCls(self, opts.get('generator-args'))

        res = super().run()

        res[0]['classes'].extend(classes)
        return res

    def get_csv_data(self):
        if self.generator is None:
            return super().get_csv_data()
        
        table = self.generator.run()
        source = type(self.generator).__name__

        return rstutils.csvlines(table), source


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



    # config[ConfKey.jenv].loader.searchpath = paths

def setup(app: Sphinx):

    app.add_config_value(ConfKey.truth_table_template, 'truth_table.jinja2', 'env', [str])
    app.add_config_value(ConfKey.truth_table_reverse, True, 'env', [bool])
    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('tableau', Tableaud)
    app.add_directive('truth-table', TruthTable)
    app.add_directive('truth-tables', TruthTables)

