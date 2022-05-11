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

from typing import TYPE_CHECKING, Literal

import sphinx.directives.other
import sphinx.directives.patches
from docutils import nodes
from pytableaux import examples, logics, models, tools
from pytableaux.lang import (Atomic, Argument, LexWriter, Marking, Notation, Operator, Parser,
                             Predicates, RenderSet)
from pytableaux.proof import rules, writers, Tableau, TabWriter
from pytableaux.proof.helpers import EllipsisExampleHelper
from pytableaux.tools.doc import (BaseDirective, DirectiveHelper, RenderMixin,
                                  SphinxEvent, boolopt, choiceopt, classopt,
                                  flagopt, opersopt, predsopt, re_comma,
                                  rstutils, stropt)
from pytableaux.tools.doc.extension import ConfKey
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any

    import sphinx.config
    from pytableaux.tools.doc import Tabler
    from sphinx.application import Sphinx

__all__ = (
    'CSVTable',
    'Include',
    'TableauDirective',
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


class TableauDirective(BaseDirective):
    """Tableau directive.
    

    For an argument::

        .. tableau::
             :logic: FDE
             :conclusion: B
             :premises: A, A > B

        .. tableau::
             :logic: FDE
             :argument: Modus Ponens
    
    For rule example::

        .. tableau::
            :logic: CFOL
            :rule: Conjunction
    
    For a build_trunk example::

        .. tableau::
            :logic: FDE
            :build-trunk:
    """

    optional_arguments = 1

    option_spec = dict(

        logic = logics.registry,
        format = choiceopt(writers.registry),
        wnotn = Notation,
        classes = classopt,

        # argument mode
        argument = examples.argument,
        conclusion = stropt,
        premises = re_comma.split,
        pnotn = Notation,
        preds = predsopt,

        # rule mode
        rule = stropt,

        # build-trunk mode
        **{'build-trunk': flagopt,},
        prolog = flagopt,


    )

    modes = {
        'rule'        : {'rule'},
        'build-trunk' : {'build-trunk', 'prolog'},
        'argument'    : {'argument', 'conclusion', 'premises', 'pnotn', 'preds'},
    }
    opts_for_argument = {'argument', 'conclusion', 'premises', 'pnotn', 'preds'}
    trunk_argument = Argument(Atomic(1, 0), map(Atomic, ((0, 1), (0, 2))))

    def run(self):

        opts = self.options
        conf = self.config
        opts['classes'] = classes = self.set_classes()
        nlist = []

        if 'logic' not in opts:
            opts['logic'] = self.current_logic()

        wfmt = opts.setdefault('format', 'html')
        wnotn = opts['wnotn'] = Notation[opts.get('wnotn', conf[ConfKey.wnotn])]

        charset = writers.registry[wfmt].default_charsets[wnotn]
        renderset = RenderSet.fetch(wnotn, charset)

        mode = self._check_options_mode()

        if mode == 'argument':
            tab = self.gettab_argument()
        else:
            classes |= mode, 'example'

            if mode == 'rule':
                tab = self.gettab_rule()
            else:
                assert mode == 'build-trunk'
                tab =  self.gettab_trunk()
                if 'prolog' in opts:
                    nlist.append(nodes.container('',
                        *self.getnodes_trunk_prolog(),
                        classes = classes + ['prolog'],
                    ))
                # change renderset
                renderset = self.get_trunk_renderset(wnotn, charset)

        lw = LexWriter(wnotn, renderset = renderset)

        tab.build()
        writer = TabWriter(wfmt, lw = lw, classes = classes)

        output = writer(tab)

        if wfmt == 'html':
            nlist.append(nodes.raw(format = 'html', text = output))
        else:
            classes |= 'tableau',
            nlist.append(nodes.literal_block(text = output, classes = classes))

        return nlist


    def gettab_rule(self):

        opts = self.options

        tab = Tableau(opts['logic'])
        rule = tab.rules.get(opts['rule'])

        # if isinstance(rule, rules.ClosingRule):
        #     classes |= ['closure']
        # else:
        #     pass
        if not isinstance(rule, rules.ClosingRule):
            rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)

        tab.branch().extend(rule.example_nodes())

        return tab

    def gettab_argument(self):

        opts = self.options
        conf = self.config
        try:
            if 'argument' in opts:
                if (badopts := ({'conclusion', 'premises'} & set(opts))):
                    raise self.error(f"Option not allowed with 'argument': {badopts}")
                arg = opts['argument']
            else:
                pnotn = opts.get('pnotn', conf[ConfKey.pnotn])
                preds = Predicates(opts.get('preds', conf[ConfKey.preds]))
                parser = Parser(pnotn, preds)
                arg = parser.argument(opts['conclusion'], opts.get('premises'))
        except KeyError as e:
            raise self.error(f'Missing required option: {e}')

        return Tableau(opts['logic'], arg)

    def gettab_trunk(self):
        tab = Tableau(self.options['logic'])
        # Pluck a rule.
        rule = tab.rules.groups[1][0]
        # Inject the helper.
        rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
        # Build trunk.
        tab.argument = self.trunk_argument
        return tab

    def getnodes_trunk_prolog(self):
        # HTML subscripts don't get escaped
        notn = self.options['wnotn']
        renderset = self.get_trunk_renderset(notn, 'unicode')
        lw = LexWriter(notn, renderset = renderset)
        c, p1, p2 = map(lw, self.trunk_argument)
        return nodes.container('',
            nodes.inline('', text = 'For the argument'),
            nodes.inline('', text = f'{p1} ... {p2} ∴ {c}', classes = ['argument']),
            nodes.inline('', text = 'add:')
        )

    @classmethod
    def get_trunk_renderset(cls, notn, charset):
        # Make a RenderSet that renders subscript 2 as 'n'.
        rskey = f'{__name__}.{charset}.trunk'
        try:
            return RenderSet.fetch(notn, rskey)
        except KeyError:
            pass
        prev = RenderSet.fetch(notn, charset)
        def rendersub(sub):
            if sub == 2:
                sub = 'n'
            return prev.string(Marking.subscript, sub)
        data = dict(prev.data)
        data.update(renders = dict(data['renders']) | {
            Marking.subscript: rendersub
        })
        return RenderSet.load(notn, rskey, data)

    def _check_options_mode(self) -> Literal['argument']|Literal['rule']|Literal['build-trunk']:
        opts = self.options
        for mode in ('rule', 'build-trunk'):
            if mode in opts:
                break
        else:
            return 'argument'
        badopts = self.modes['argument'] & set(opts)
        if mode == 'rule' and 'build-trunk' in opts:
            badopts.add('build-trunk')
        if badopts:
            raise self.error(f"Option(s) not allowed with '{mode}': {badopts}")
        return mode

# class TruthTable(BaseDirective, RenderMixin):
#     'Truth table (raw html).'

#     #: <Logic>.<Operator>
#     required_arguments = 1

#     option_spec = dict(
#         wnotn = Notation,
#         template = stropt,
#         reverse = boolopt,
#         clear = boolopt,
#         classes = classopt,
#     )

#     def run(self):

#         classes = self.set_classes()
#         opts = self.options
#         conf = self.config

#         argstr, = self.arguments
#         try:
#             logic, oper = argstr.split('.')
#             logic = logics.registry(logic)
#             model: models.BaseModel = logic.Model()
#             oper = Operator(oper)
#         except Exception as e:
#             logger.error(e)
#             raise self.error(f'Bad operator argument: {argstr}')

#         wnotn = opts.get('wnotn', conf[ConfKey.wnotn])
#         lw = LexWriter(wnotn, 'html')

#         template = opts.get('template', conf[ConfKey.truth_table_template])
#         reverse = opts.get('reverse', conf[ConfKey.truth_table_reverse])
#         clear = opts.get('clear', True)

#         table = model.truth_table(oper, reverse = reverse)
#         context = dict(table = table, lw = lw, classes = classes)
#         content = self.render(template, context)
#         if clear:
#             content += '<div class="clear"></div>'

#         return [nodes.raw(format = 'html', text = content)]

class TruthTables(BaseDirective, RenderMixin):
    'Truth tables (raw html) of all operators.'

    #: Logic
    # optional_arguments = 1

    option_spec = dict(
        logic = logics.registry,
        operators = opersopt,
        wnotn = Notation,
        template = stropt,
        reverse = boolopt,
        clear = boolopt,
        classes = classopt,
    )

    def run(self):

        classes = self.set_classes()
        opts = self.options
        conf = self.config

        if 'logic' not in opts:
            opts['logic'] = self.current_logic()

        # if len(self.arguments):
        #     logic = logics.registry(self.arguments[0])
        # else:
        #     logic = self.current_logic()

        model: models.BaseModel = opts['logic'].Model()
        opers = opts.get('operators')
        if opers is None:
            opers = sorted(model.truth_functional_operators)

        wnotn = opts.get('wnotn', conf[ConfKey.wnotn])
        lw = LexWriter(wnotn, 'html')

        template = opts.get('template', conf[ConfKey.truth_table_template])
        reverse = opts.get('reverse', conf[ConfKey.truth_table_reverse])
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



def setup(app: Sphinx):

    app.add_config_value(ConfKey.wnotn,'standard', 'env', [str, Notation])
    app.add_config_value(ConfKey.pnotn, 'standard', 'env', [str, Notation])
    app.add_config_value(ConfKey.preds,
        ((0,0,1), (1,0,1), (2,0,1)), 'env', [tuple, Predicates])

    app.add_config_value(ConfKey.truth_table_template, 'truth_table.jinja2', 'env', [str])
    app.add_config_value(ConfKey.truth_table_reverse, True, 'env', [bool])

    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('tableau', TableauDirective)
    # app.add_directive('truth-table', TruthTable)
    app.add_directive('truth-tables', TruthTables)

