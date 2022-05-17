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
import sys
from typing import TYPE_CHECKING

import sphinx.directives.code
import sphinx.directives.other
import sphinx.directives.patches
from docutils import nodes
from docutils.statemachine import StringList
from pytableaux import examples, logics, models, tools
from pytableaux.lang import (Argument, Atomic, LexWriter, Marking,
                             Notation, Operator, Predicate, Predicates,
                             Quantifier, RenderSet)
from pytableaux.proof import Tableau, TabWriter, writers
from pytableaux.tools.doc import (BaseDirective, ConfKey, DirectiveHelper,
                                  ParserOptionMixin, RenderMixin, SphinxEvent,
                                  attrsopt, boolopt, choice_or_flag, choiceopt,
                                  classopt, flagopt, nodez, opersopt, predsopt,
                                  re_comma, snakespace, stropt)
from pytableaux.tools.doc.misc import EllipsisExampleHelper, rules_sorted
from pytableaux.tools.doc.nodez import block
from pytableaux.tools.hybrids import qset
from pytableaux.tools.sets import EMPTY_SET
from sphinx import addnodes
from sphinx.ext.viewcode import viewcode_anchor
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any, Literal

    import sphinx.config
    from docutils import nodes
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


class SentenceBlock(BaseDirective, ParserOptionMixin):
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

        parser = self.parser_option()

        text = '\n'.join(self.content)     

        literal = nodes.inline(classes = ['pre'])

        wnotn = opts.get('wnotn', conf[ConfKey.wnotn])

        if ':=' in text:
            s1, s2 = map(parser, text.split(':='))
            literal += [
                nodez.sentence(sentence = s1, notn = wnotn),
                nodes.inline(' ', ' '),
                nodes.math(':=', ':='),
                nodes.inline(' ', ' '),
                nodez.sentence(sentence = s2, notn = wnotn)
            ]
        else:
            literal += nodez.sentence(sentence = parser(text), notn = wnotn)
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

    def _parse_caption(self, node: nodes.Element):
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

class TableauDirective(BaseDirective, ParserOptionMixin):
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
        ruledoc = flagopt,

        # build-trunk mode
        **{'build-trunk': flagopt,},
        prolog = flagopt,

    )

    if TYPE_CHECKING:
        ...

    modes = {
        'rule'        : {'rule', 'legend', 'ruledoc'},
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

    mode: str
    charset: str
    renderset: RenderSet
    writer: TabWriter
    lwuni: LexWriter

    _setup: bool = False

    def setup(self, force = False):

        if self._setup and not force:
            return
        self._setup = True

        opts = self.options
        conf = self.config
        opts['classes'] = classes = self.set_classes()

        if 'logic' not in opts:
            opts['logic'] = self.current_logic()

        wformat = opts.setdefault('format', 'html')
        opts['wnotn'] = wnotn = Notation[opts.get('wnotn', conf[ConfKey.wnotn])]

        self.mode = self._check_options_mode()
        classes.add(self.mode)

        self.charset = writers.registry[wformat].default_charsets[wnotn]
        if self.mode == 'build-trunk':
            self.renderset = self.get_trunk_renderset(wnotn, self.charset)
        else:
            self.renderset = RenderSet.fetch(wnotn, self.charset)

        self.writer = TabWriter(wformat,
            lw = LexWriter(wnotn, renderset = self.renderset),
            classes = classes, wrapper = False
        )
        self.lwuni = LexWriter(wnotn, 'unicode')

    def run(self):

        self.setup()

        opts = self.options
        classes: qset[str] = opts['classes']

        if self.mode == 'argument':
            tab = self.gettab_argument()
        else:
            classes.add('example')
            if self.mode == 'rule':
                tab = self.gettab_rule()
                rule: Rule = tab.rules.get(opts['rule'])
                rulecls = type(rule)
            else:
                assert self.mode == 'build-trunk'
                tab = self.gettab_trunk()

        if self.mode == 'rule':
            tab.step()
            tab.finish()
        else:
            tab.build()

        output = self.writer(tab)
    
        if opts['format'] == 'html':
            tabnode = nodes.raw(format = 'html', text = output)
        else:
            tabnode = nodes.literal_block(text = output,
                classes = ['tableau'])

        tabwrapper = nodes.container(
            classes = ['tableau-wrapper'] + classes
        )

        if self.mode == 'rule':


            if 'ruledoc' in opts:
                if 'legend' in opts:
                    legend = nodes.inline(classes = ['rule-legend'])
                    legend += self.getnodes_rule_legend(rule)
                else:
                    legend = EMPTY_SET
                docwrapper, container = self.getnodes_ruledoc_pair(rulecls, legend)
                container += tabwrapper
                tabwrapper += tabnode

                if 'legend' in opts:
                    docwrapper['classes'].append('with-legend')
                return [docwrapper]

            if 'legend' in opts:
                legend = nodes.container(classes = ['rule-legend'])
                legend += self.getnodes_rule_legend(rule)
                tabwrapper += legend
            
            tabwrapper += tabnode
            return [tabwrapper]
        
        if 'prolog' in opts:
            prolog = nodes.container(classes = ['prolog'])
            prolog += self.getnodes_trunk_prolog()
            tabwrapper += prolog

        tabwrapper += tabnode
        return [tabwrapper]

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
        return tab

    def gettab_argument(self):
        opts = self.options
        if 'argument' in opts:
            arg = opts['argument']
        else:
            parser = self.parser_option()
            arg = parser.argument(opts['conclusion'], opts.get('premises'))
        return Tableau(opts['logic'], arg)

    def gettab_trunk(self):
        tab = Tableau(self.options['logic'])
        rule = tab.rules.groups[1][0]
        helper = EllipsisExampleHelper(rule)
        rule.helpers[type(helper)] = helper
        tab.argument = self.trunk_data['arg']
        return tab

    def getnode_ruledoc_wrapper(self, rulecls: type[Rule], *inserts) -> addnodes.desc:
        """Usage::
        
            wrapper = self.getnode_ruledoc_wrapper(rulecls)
            container = addnodes.desc_content()
            wrapper += container
            container += ...
        """
        modname = rulecls.__module__
        refid = rulecls.__qualname__
        fullid = f'{modname}.{refid}'
        domain = 'py'
        objtype = 'object'

        sigtext = snakespace(rulecls.name)

        signame = addnodes.desc_name(classes = ['pre', 'ruledoc', 'rule-sig'])
        signame += (nodes.inline(rulecls.name, sigtext, classes = ['ruledoc', 'rule-sig']),
            viewcode_anchor(refdomain = domain, reftype = objtype, 
                refdoc = self.env.docname, refid = refid,
                reftarget = self.viewcode_target(rulecls), classes=['ruledoc']))

        wrapper = addnodes.desc(domain = domain, objtype = objtype,
                    classes = [domain, objtype, 'ruledoc'])
        sig = addnodes.desc_signature(ids = [fullid], classes = ['ruledoc'])

        wrapper += sig
        sig += inserts
        sig += signame

        return wrapper

    def getnodes_ruledoc_pair(self, rulecls: type[Rule], *inserts) -> tuple[addnodes.desc, addnodes.desc_content]:
        wrapper = self.getnode_ruledoc_wrapper(rulecls, *inserts)
        container = addnodes.desc_content()
        wrapper += container
        return wrapper, container

    def getnodes_rule_legend(self, rule: Rule|type[Rule]):
        nn = []
        legend = rule.legend
        lw = self.lwuni
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
            nn.append(nodes.inline(text, text,
                classes = ['legend-item', name],))
        return nn

    def getnodes_trunk_prolog(self):
        # Plain docutils nodes, not raw html.
        # notn = self.options['wnotn']
        # renderset = self.get_trunk_renderset(notn)#, 'unicode')
        # renderset = RenderSet.fetch(notn, 'unicode')
        # lw = self.lwuni
        opts = self.options
        # refdata = self.trunk_data
        # arg = refdata['arg']
        # unstr, cstr = map(lw, (refdata['unsub'], arg.conclusion))
        argnode = nodes.inline(classes = ['argument'], notn = opts['wnotn'])
        # pnodes = (nodes.inline('', unstr, subnode) for subnode in refdata['subnodes'])
        prem2 = nodez.sentence(sentence = Atomic(0,0), notn = opts['wnotn'])
        prem2 += nodes.subscript('n', 'n')
        argnode += (
            # next(pnodes),
            nodez.sentence(sentence = Atomic(0,1), notn = opts['wnotn']),
            nodes.inline(text = ' ... '),
            # next(pnodes),
            prem2,
            nodes.inline(text = ' ∴ '),
            # nodes.inline(text = f' ∴ {cstr}'),
            nodez.sentence(sentence = Atomic(1, 0), notn = opts['wnotn'])
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

    def _check_options_mode(self) -> Literal['argument','rule','build-trunk']:
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


class RuleGroupDirective(TableauDirective):
    """
    Example::

        .. tableau-rules::
            :group: quantifier
            :legend:
            :title: Quantifier Rules
            :titles:
    """
    optional_arguments = sys.maxsize
    option_spec = dict(

        # Common
        logic   = logics.registry,
        format  = choiceopt(writers.registry),
        wnotn   = Notation,
        classes = classopt,

        title  = stropt,
        titles = choice_or_flag({'symbols', 'names', 'labels'}, default = 'symbols'),
        flat   = flagopt,

        group    = choiceopt({'closure', 'operator', 'quantifier', 'predicate', 'ungrouped'}),
        exclude  = attrsopt,
        include  = attrsopt,
        subgroup = stropt,
        legend   = flagopt,
        captions = flagopt,
        docs     = flagopt,

    )

    groupmode: str

    ruleinfo: dict[str, Any]
    title: str|None
    group: list[type[Rule]]|None
    subgroups: dict[Predicate|Quantifier|Operator, list[type[Rule]]]|None
    exclude: set[str]
    include: set[str]|None
    groupid: str
    subgroup: list[type[Rule]]|None
    subgroup_type: type[Predicate|Quantifier|Operator]|None

    def setup(self):

        super().setup()

        opts = self.options
        if 'subgroup' in opts:
            label = f"{opts['subgroup']} Rules"
        else:
            label = f"{opts['group'].capitalize()} Rules"
        self.groupid = label.lower().replace(' ', '-')
        if opts.get('title'):
            self.title = opts['title']
        elif 'title' in opts:
            self.title = label
        else:
            self.title = None
        
        self.exclude = set(opts.get('exclude', EMPTY_SET))
        self.include = opts.get('include')
        if self.include is not None:
            self.include = set(self.include)

        self.ruleinfo = info = rules_sorted(opts['logic'])
        group: list[type[Rule]] = info['legend_groups'][opts['group']]

        subgroups = info['legend_subgroups'].get(opts['group'])

        if 'subgroup' in opts:
            if opts['subgroup'] not in info['subgroup_types']:
                raise self.error('Unknown subgroup: %s' % opts['subgroup'])
            self.groupmode = 'subgroup'
            self.subgroup_type = info['subgroup_types'][opts['subgroup']]
            self.subgroup = self.subgroup_type(opts['subgroup'])

        elif not subgroups or 'flat' in opts or opts['group'] == 'ungrouped':
            self.groupmode = 'group'
            self.group = group

        else:
            self.groupmode = 'subgroups'
            self.subgroups = subgroups

        if 'docs' in opts:
            opts['ruledoc'] = opts['docs']

    def run(self):

        self.setup()

        opts = self.options
        classes: qset[str] = opts['classes']
        exclude = self.exclude

        nlist = []

        if self.groupmode == 'subgroups':
            for obj, subgroup in self.subgroups.items():
                if obj.name in exclude:
                    continue
                if self.include and obj.name not in self.include:
                    continue
                cont = nodes.section(
                    classes = ['tableau-rule-subgroup'],
                    ids = [f'{obj.name.lower()}-rules'],
                )
                if 'titles' in opts:
                    if (o := opts['titles']) == 'labels':
                        prefix = getattr(obj, 'label', obj.name)
                    elif o == 'names':
                        prefix = obj.name
                    else:
                        prefix = self.lwuni(obj)
                    cont += nodes.title(text = f'{prefix} Rules')
                for rule in subgroup:
                    if rule.name in exclude:
                        continue
                    opts['rule'] = rule.name
                    if 'captions' in opts:
                        opts['caption'] = snakespace(rule.name)
                    else:
                        opts.pop('caption', None)
                    cont += super().run()
                nlist.append(cont)
        else:
            if self.groupmode == 'subgroup':
                rules = self.subgroup
                classes.add('tableau-rule-subgroup')
            else:
                assert self.groupmode == 'group'
                rules = self.group
                classes.add('tableau-rule-group')
            for rule in rules:
                if rule.name in exclude:
                    continue
                if self.include and rule.name not in self.include:
                    continue
                opts['rule'] = rule.name
                if 'captions' in opts:
                    opts['caption'] = snakespace(rule.name)
                else:
                    opts.pop('caption', None)
                nlist.extend(super().run())

        if self.title:
            nodecls = nodes.section
        else:
            nodecls = nodes.container
        cont = nodecls(
            classes = classes,
            ids = [self.groupid],
        )
        if self.title:
            cont += nodes.title(text = self.title)

        cont += nlist
        return [cont]

    def _check_options_mode(self):
        if 'group' not in self.options:
            raise self.error(f"Missing required option: group")
        return 'rule'



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
    app.add_config_value(ConfKey.charset, None, 'env', [str])
    app.add_config_value(ConfKey.rset, None, 'env', [str])
    app.add_config_value(ConfKey.truth_table_template, 'truth_table.jinja2', 'env', [str])
    app.add_config_value(ConfKey.truth_table_reverse, True, 'env', [bool])

    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('tableau', TableauDirective)
    app.add_directive('tableau-rules', RuleGroupDirective)
    app.add_directive('truth-tables', TruthTables)
    app.add_directive('sentence', SentenceBlock)



# docwrapper = nodes.definition_list(classes = ['py', 'class'])
# docwrapper += (litem := nodes.definition_list_item())
# litem  += (fields := nodes.field_list())
# fields += (field := nodes.field())
# field  += (dt := nodes.field_name(
#     classes = ['sig','sig-object','py']
# ))
# field  += (dd := nodes.field_body())
# dt += nodes.inline('', '',
#     nodes.inline(text = rule.name, classes = ['pre']),
#     classes = ['sig-name', 'descname'],
# )
# dd += tabwrapper
# return [
#     docwrapper
# ]
