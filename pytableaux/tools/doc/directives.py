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
import csv

from typing import TYPE_CHECKING

import sphinx.directives.code
import sphinx.directives.other
import sphinx.directives.patches
from docutils import nodes
from docutils.statemachine import StringList
from pytableaux import examples, logics, models, tools
from pytableaux.lang import (Argument, Atomic, LexWriter, Marking, Notation,
                             Parser, Predicates, RenderSet)
from pytableaux.proof import Tableau, TabWriter, writers
from pytableaux.tools.doc import (BaseDirective, ConfKey, DirectiveHelper,
                                  RenderMixin, SphinxEvent, boolopt, choiceopt,
                                  classopt, extnodes, flagopt, opersopt,
                                  predsopt, re_comma, roles, stropt)
from pytableaux.tools.doc.extnodes import block
from pytableaux.tools.doc.misc import EllipsisExampleHelper, rule_legend
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any, overload, Literal

    import sphinx.config
    from pytableaux.proof import Rule
    from pytableaux.tools.doc import Tabler
    from sphinx.application import Sphinx

__all__ = (
    'CSVTable',
    'Include',
    'SentenceBlock',
    'TableauDirective',
    'TableGenerator',
    'TruthTables',
    'table_generators',
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


class SentenceBlock(BaseDirective):
    """Sentence literal block directive.
    
    Example::

        .. sentence::
            :caption: If `A`, then `B`

            A > B
    
    For a definition::

        .. sentence::
            :defn:

            A < B := (A > B) & (B > A)
    """

    has_content = True
    option_spec = dict(
        defn = flagopt,

        wnotn   = Notation,
        classes = classopt,

        pnotn = Notation,
        preds = predsopt,

        caption = stropt,
    )

    def run(self):

        classes = self.set_classes()
        classes |= 'highlight', 'notranslate'

        opts = self.options
        conf = self.config

        preds = Predicates(opts.get('preds', conf[ConfKey.preds]))
        parser = Parser(opts.get('pnotn', conf[ConfKey.pnotn]), preds)
        lw = LexWriter(opts.get('wnotn', conf[ConfKey.wnotn]), 'unicode')

        text = '\n'.join(self.content)     

        literal = nodes.inline(classes = ['pre'])

        if ':=' in text:
            a, b = map(lw, map(parser, text.split(':=')))
            literal += [
                extnodes.sentence(a, a + ' '),
                nodes.math(':=', ':='),
                extnodes.sentence(b, ' ' + b)
            ]
        else:
            literal += extnodes.sentence(text, lw(parser(text)))

        cont = nodes.container(
            literal_block = True,
            classes = classes
        )

        cont += self._parse_caption(literal)
        cont += literal

        wrapper = block(
            classes = ['highlight-sentence', 'literal-block-wrapper']
        )
        wrapper += cont
        return [wrapper]

    def _parse_caption(self, node):
        # sphinx.directives.code
        # cont = self.container_wrapper(literal, line)
        line = self.options.get('caption')
        if not line:
            return []
        parsed = nodes.Element()
        self.state.nested_parse(StringList([line], source=''),
                                self.content_offset, parsed)
        if isinstance(parsed[0], nodes.system_message):
            raise ValueError('Invalid caption: %s' % parsed[0].astext())
        caption = nodes.caption(parsed[0].rawsource, '',
            *parsed[0].children, classes = ['code-block-caption'])
        caption.source = node.source
        caption.line = node.line
        return caption

class TableauDirective(BaseDirective):
    """Tableau directive.
    

    For an argument::

        .. tableau::
             :logic: FDE
             :argument: Modus Ponens

        .. tableau::
             :logic: FDE
             :conclusion: Gb
             :premises: Fac, Fac > Gb
             :pnotn: standard
             :preds: 0,0,2 : 1,0,1
    
    For rule example::

        .. tableau::
            :logic: CFOL
            :rule: Conjunction
    
    For a build_trunk example::

        .. tableau::
            :logic: FDE
            :build-trunk:
            :prolog:
    """

    option_spec = dict(

        # Common
        logic   = logics.registry,
        format  = choiceopt(writers.registry),
        wnotn   = Notation,
        classes = classopt,

        # argument mode
        argument = examples.argument,
        conclusion = stropt,
        premises = re_comma.split,
        pnotn = Notation,
        preds = predsopt,

        # rule mode
        rule = stropt,
        legend = flagopt,

        # build-trunk mode
        **{'build-trunk': flagopt,},
        prolog = flagopt,

    )

    if TYPE_CHECKING:
        ...

    modes = {
        'rule'        : {'rule', 'legend'},
        'build-trunk' : {'build-trunk', 'prolog'},
        'argument'    : {'argument', 'conclusion', 'premises', 'pnotn', 'preds'},
        ... : {'format', 'classes', 'wnotn', 'logic'},
    }
    trunk_data = dict(
        arg = (arg := Argument(Atomic(1, 0), map(Atomic, ((0, 1), (0, 2))))),
        unsub = Atomic(0, 0),
        subnodes = (*(nodes.subscript(text = str(s))
            for s in ('1', 'n')),),
    )
    def run(self):

        opts = self.options
        conf = self.config
        opts['classes'] = classes = self.set_classes()
        nlist = []

        if 'logic' not in opts:
            opts['logic'] = self.current_logic()

        wformat = opts.setdefault('format', 'html')
        opts['wnotn'] = wnotn = Notation[opts.get('wnotn', conf[ConfKey.wnotn])]

        charset = writers.registry[wformat].default_charsets[wnotn]
        renderset = RenderSet.fetch(wnotn, charset)

        mode = self._check_options_mode()
        classes.add('mode')

        if mode == 'argument':
            tab = self.gettab_argument()

        else:
            classes.add('example')

            if mode == 'rule':
                tab = self.gettab_rule()
                rule = tab.rules.get(opts['rule'])
                if 'legend' in opts:
                    n = nodes.container(classes = ['rule-legend'])
                    n += self.getnodes_rule_legend(rule)
                    nlist.append(n)
            else:
                assert mode == 'build-trunk'
                tab =  self.gettab_trunk()
                if 'prolog' in opts:
                    n = nodes.container(classes = ['prolog'])
                    n += self.getnodes_trunk_prolog()
                    nlist.append(n)
                # change renderset
                renderset = self.get_trunk_renderset(wnotn, charset)

        writer = TabWriter(wformat,
            lw = LexWriter(wnotn, renderset = renderset),
            classes = classes, wrapper = False
        )

        if mode == 'rule':
            tab.step()
            tab.finish()
        else:
            tab.build()

        output = writer(tab)

        if wformat == 'html':
            nlist.append(nodes.raw(format = 'html', text = output))
        else:
            classes |= 'tableau',
            nlist.append(nodes.literal_block(text = output, classes = classes))

        cont = nodes.container(
            classes = ['tableau-wrapper'] + classes
        )
        cont += nlist
        return [cont]

    def gettab_rule(self):
        opts = self.options
        tab = Tableau()
        logic: logics.LogicType = opts['logic']
        rulecls = getattr(logic.TabRules, opts['rule'])
        tab.rules.append(rulecls)
        rule = tab.rules[0]
        helper = EllipsisExampleHelper(rule)
        rule.helpers[type(helper)] = helper
        tab.branch().extend(rule.example_nodes())
        # tab = Tableau(opts['logic'])
        # rule: Rule = tab.rules.get(opts['rule'])
        # rule.helpers[EllipsisExampleHelper] = EllipsisExampleHelper(rule)
        # tab.branch().extend(rule.example_nodes())
        return tab

    def gettab_argument(self):
        opts = self.options
        conf = self.config
        if 'argument' in opts:
            arg = opts['argument']
        else:
            pnotn = opts.get('pnotn', conf[ConfKey.pnotn])
            preds = Predicates(opts.get('preds', conf[ConfKey.preds]))
            arg = Parser(pnotn, preds).argument(
                opts['conclusion'], opts.get('premises'))
        return Tableau(opts['logic'], arg)

    def gettab_trunk(self):
        tab = Tableau(self.options['logic'])
        # Pluck a rule.
        rule = tab.rules.groups[1][0]
        # Inject the helper.
        helper = EllipsisExampleHelper(rule)
        rule.helpers[type(helper)] = helper
        # Build trunk.
        tab.argument = self.trunk_data['arg']
        return tab

    def getnodes_rule_legend(self, rule):
        nn = []
        opts = self.options
        legend = rule_legend(rule)
        lw = LexWriter(opts['wnotn'], 'unicode')
        renderset = lw.renderset
        for name, value in legend:
            if lw.canwrite(value):
                text = lw(value)
            else:
                try:
                    text = renderset.string(Marking.tableau, (name, value))
                except KeyError:
                    raise self.error(
                        f'Unwriteable legend item: {(name, value)} for {rule}')
            nn.append(nodes.inline(text, text, classes = ['legend-item', name]))
 
        cont = nodes.container()
        # ref = roles.refplus()
        # si = self.get_source_info()
        # n = nodes.caption()
        # r = ref('ref', f':ref:`{rule.name}`', rule.name, si[1], self.state.inliner, {}, {})
        # self.state.inliner
        # n += nodes.literal(text = rule.name)
        # cont += n
        # nn.append(cont)
        return nn

    def getnodes_trunk_prolog(self):
        # Plain docutils nodes, not raw html.
        notn = self.options['wnotn']
        # renderset = self.get_trunk_renderset(notn)#, 'unicode')
        renderset = RenderSet.fetch(notn, 'unicode')
        lw = LexWriter(notn, renderset = renderset)
        refdata = self.trunk_data
        arg = refdata['arg']
        unstr, cstr = map(lw, (refdata['unsub'], arg.conclusion))
        argnode = nodes.inline(classes = ['argument'])
        pnodes = (nodes.inline('', unstr, subnode) for subnode in refdata['subnodes'])
        argnode += (
            next(pnodes),
            nodes.inline(text = ' ... '),
            next(pnodes),
            nodes.inline(text = f' ∴ {cstr}'),
        )
        return [
            nodes.inline(text = 'For the argument '),
            argnode,
            nodes.inline(text = ' write:'),
        ]

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
        for mode, names in self.modes.items():
            if mode in opts:
                break
        else:
            if 'argument' in opts:
                if (badopts := ({'conclusion', 'premises'} & set(opts))):
                    raise self.error(f"Option not allowed with 'argument': {badopts}")
            elif 'conclusion' not in opts:
                raise self.error(f'Missing required option: conclusion')
            return 'argument'
        badopts = set(opts).difference(names).difference(self.modes[...])
        if badopts:
            raise self.error(f"Option(s) not allowed with '{mode}': {badopts}")
        return mode




class TruthTables(BaseDirective, RenderMixin):
    'Truth tables (raw html).'

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

        nlist = [nodes.raw(format = 'html', text = content)]
        if clear:
            nlist.append(block(classes = ['clear']))

        return nlist





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

        return self.csvlines(table), source

    class _writeshim:
        'Make any function into  a ``write()`` method.'
        __slots__ = 'write',

        def __init__(self, func):
            self.write = func

    @classmethod
    def csvlines(cls, rows: list[list[str]], /, quoting = csv.QUOTE_ALL, **kw) -> list[str]:
        'Format rows as CSV lines.'
        lines = []
        w = csv.writer(cls._writeshim(lines.append), quoting = quoting, **kw)
        w.writerows(rows)
        return lines


class Include(sphinx.directives.other.Include, BaseDirective):
    "Override include directive to inject include-read event."

    class StateMachineProxy:

        __slots__ = 'insert_input', '_origin',

        def __getattr__(self, name):
            return getattr(self._origin, name)

        def __setattr__(self, name, value):
            if name in self.__slots__:
                super().__setattr__(name, value)
            else: 
                setattr(self._origin, name, value)

    def run(self):

        origin = self.state_machine

        def intercept(lines, source):
            self.app.emit(SphinxEvent.IncludeRead, lines)
            return origin.insert_input(lines, source)

        self.state_machine = proxy = self.StateMachineProxy()

        proxy._origin = origin
        proxy.insert_input = intercept

        try:
            return super().run()
        finally:
            self.state_machine = origin
            del(proxy._origin, proxy.insert_input)



def setup(app: Sphinx):

    app.add_config_value(ConfKey.wnotn,'standard', 'env', [str, Notation])
    app.add_config_value(ConfKey.pnotn,'standard', 'env', [str, Notation])
    app.add_config_value(ConfKey.preds,
        ((0,0,1), (1,0,1), (2,0,1)), 'env', [tuple, Predicates])

    app.add_config_value(ConfKey.truth_table_template, 'truth_table.jinja2', 'env', [str])
    app.add_config_value(ConfKey.truth_table_reverse, True, 'env', [bool])

    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('tableau', TableauDirective)
    app.add_directive('truth-tables', TruthTables)
    app.add_directive('sentence', SentenceBlock)


