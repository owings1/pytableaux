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
pytabdoc.directives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from __future__ import annotations

import csv
import sys
from abc import abstractmethod
from typing import Iterable, Iterator, Literal, TypeVar

import sphinx.config
import sphinx.directives.code
import sphinx.directives.other
import sphinx.directives.patches
from docutils import nodes
from docutils.statemachine import StringList
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.ext.viewcode import viewcode_anchor
from sphinx.util import logging

from pytableaux import examples, logics
from pytableaux.lang import (Argument, Atomic, LexWriter,
                             Marking, Notation, Operated, Operator, Predicate,
                             Predicates, Quantifier)
from pytableaux.proof import Rule, Tableau, TabWriter, writers, rules, helpers
from pytableaux.tools import EMPTY_SET, inflect, qset

from . import (BaseDirective, ConfKey, DirectiveHelper, LogicOptionMixin,
               ParserOptionMixin, RenderMixin, SphinxEvent, Tabler, nodez,
               optspecs)
from .misc import rules_sorted
from .nodez import block
from .roles import refplus

__all__ = (
    'CSVTable',
    'Include',
    'SentenceBlock',
    'TableauDirective',
    'TableGenerator',
    'TruthTables',
    'table_generators')

_T = TypeVar('_T')

logger = logging.getLogger(__name__)


class TableGenerator(DirectiveHelper):
    'Table generator directive helper.'

    @abstractmethod
    def gentable(self) -> Tabler: ...

    def run(self):
        table = self.gentable()
        opts = self.options
        opts.setdefault('header-rows', 1)
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
        defn = optspecs.flag,
        wnotn = Notation,
        classes = optspecs.classes,
        pnotn = Notation,
        preds = optspecs.preds,
        caption = optspecs.string)

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
                nodez.sentence(sentence = s2, notn = wnotn)]
        else:
            literal += nodez.sentence(sentence = parser(text), notn = wnotn)
        cont = nodes.container(
            literal_block = True,
            classes = classes)

        cont += self._parse_caption(literal)
        cont += literal

        wrapper = block(
            classes = ['highlight-sentence', 'literal-block-wrapper'])
        wrapper += cont
        return [wrapper]

    def _parse_caption(self, node: nodes.Element):
        # sphinx.directives.code
        # cont = self.container_wrapper(literal, line)
        line = self.options.get('caption')
        if not line:
            return []
        parsed = nodes.Element()
        self.state.nested_parse(
            StringList([line], source=''),
            self.content_offset,
            parsed)
        if isinstance(parsed[0], nodes.system_message):
            raise ValueError('Invalid caption: %s' % parsed[0].astext())
        caption = nodes.caption(parsed[0].rawsource, '',
            *parsed[0].children, classes = ['code-block-caption'])
        caption.source = node.source
        caption.line = node.line
        return caption

class TableauDirective(BaseDirective, ParserOptionMixin, LogicOptionMixin):
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
            :legend:
            :doc:
    
    For a build_trunk example::

        .. tableau::
            :logic: FDE
            :build-trunk:
            :prolog:
    """

    option_spec = dict(
        # Common
        logic = logics.registry,
        format = optspecs.choice(writers.registry),
        wnotn = Notation,
        classes = optspecs.classes,
        # argument mode
        argument = examples.argument,
        conclusion = optspecs.string,
        premises = optspecs.strings,
        pnotn = Notation,
        preds = optspecs.preds,
        # rule mode
        rule = optspecs.string,
        legend = optspecs.flag,
        doc = optspecs.flag,
        origin = optspecs.choice(['foreign'], default=None),
        # build-trunk mode
        **{'build-trunk': optspecs.flag,},
        prolog = optspecs.flag)

    modes = {
        'rule'        : {'rule', 'legend', 'doc', 'origin'},
        'build-trunk' : {'build-trunk', 'prolog'},
        'argument'    : {'argument', 'conclusion', 'premises', 'pnotn', 'preds'},
        ... : {'format', 'classes', 'wnotn', 'logic'}}

    mode: str
    writer: TabWriter
    lwuni: LexWriter

    _setup: bool = False

    class LexWriterWrapper(LexWriter):

        __slots__ = {'__dict__'}
        format = None

        def __init__(self, lw: LexWriter):
            self.lw = lw
            self.notation = lw.notation
            self.strings = lw.strings
            self.format = lw.format

        def _write_operated(self, item: Operated) -> str:
            return self.lw._write_operated(item)

        def _write(self, item):
            if type(item) is Atomic and item.subscript == 2:
                s = Atomic(item.index, 0)
                return self.lw._write(s) + self.lw._write_subscript('n')
            return self.lw._write(item)

    class TrunkRuleStub(rules.NoopRule):
        Helpers = helpers.EllipsisExampleHelper,

    def setup(self, force = False):
        if self._setup and not force:
            return
        self._setup = True
        self.mode = self._check_options_mode()
        opts = self.options
        opts['classes'] = self.set_classes()
        opts['wnotn'] = Notation[opts.get('wnotn', self.config[ConfKey.wnotn])]
        opts.setdefault('format', 'html')
        classes: qset[str] = opts['classes']
        classes.add(self.mode)
        if self.mode in ('rule', 'build-trunk'):
            classes.add('example')
        lw = LexWriter(notation=opts['wnotn'], format=opts['format'])
        if self.mode == 'build-trunk':
            lw = self.LexWriterWrapper(lw)
        self.writer = TabWriter(opts['format'],
            lw=lw,
            classes=classes,
            wrapper=False)
        self.lwuni = LexWriter(opts['wnotn'], dialect='unicode')

    def run(self):

        self.setup()

        opts = self.options
        classes: qset[str] = opts['classes']

        if self.mode == 'argument':
            tab = self.gettab_argument()
        elif self.mode == 'rule':
            tab = self.gettab_rule()
        else:
            tab = self.gettab_trunk()

        if self.mode == 'rule':
            tab.step()
            tab.finish()
        else:
            tab.build()

        output = self.writer(tab)
    
        if opts['format'] == 'html':
            tabnode = nodes.raw(format='html', text=output)
        else:
            tabnode = nodes.literal_block(text=output, classes=['tableau'])

        tabwrapper = nodes.container(classes=['tableau-wrapper'] + classes)

        if self.mode == 'rule':

            rulecls = type(tab.rules.get(opts['rule']))

            if 'doc' in opts:
                tabwrapper += tabnode
                content = addnodes.desc_content()
                content += tabwrapper
                inserts = []
                if 'legend' in opts:
                    legend = nodes.inline(classes=['rule-legend'])
                    legend += self.getnodes_rule_legend(rulecls)
                    inserts.append(legend)
                desc = self.getnode_ruledoc_desc(rulecls, *inserts)
                desc += content
                return [desc]

            if 'legend' in opts:
                legend = nodes.container(classes=['rule-legend'])
                legend += self.getnodes_rule_legend(rulecls)
                tabwrapper += legend

            tabwrapper += tabnode
            return [tabwrapper]

        if self.mode == 'build-trunk':
            if 'prolog' in opts:
                prolog = nodes.container(classes=['prolog'])
                prolog += self.getnodes_trunk_prolog()
                tabwrapper += prolog

        tabwrapper += tabnode
        return [tabwrapper]

    def gettab_rule(self):
        tab = Tableau(self.logic)
        rulecls = type(tab.rules.get(self.options['rule']))
        tab.rules.clear()
        tab.rules.append(rulecls)
        rule = tab.rules[0]
        rule.helpers[helpers.EllipsisExampleHelper] = helpers.EllipsisExampleHelper(rule)
        tab.branch().extend(rule.example_nodes())
        return tab

    def gettab_argument(self):
        opts = self.options
        if 'argument' in opts:
            arg = opts['argument']
        else:
            parser = self.parser_option()
            arg = parser.argument(opts['conclusion'], opts.get('premises'))
        return Tableau(self.logic, arg)

    def gettab_trunk(self):
        arg = Argument(Atomic(1, 0), map(Atomic, ((0, 1), (0, 2))))
        tab = Tableau(self.logic, arg, auto_build_trunk=False)
        tab.rules.clear()
        tab.rules.append(self.TrunkRuleStub)
        tab.build_trunk()
        return tab

    def getnode_ruledoc_desc(self, rulecls: type[Rule], *inserts) -> addnodes.desc:
        """Usage::
        
            desc = self.getnode_ruledoc_desc(rulecls, *inserts)
            content = addnodes.desc_content()
            desc += content
            content += ...
        """
        opts = self.options
        domain = 'py'
        objtype = 'class'
        classes = [domain, objtype, 'ruledoc']
        if 'legend' in opts:
            classes.append('with-legend')
        refname = rulecls.__qualname__
        nodeid = f'{rulecls.__module__}.{refname}'
        refid = refname
        inserts = list(inserts)
        nametext = inflect.snakespace(rulecls.name)
        is_local = rulecls.Meta.name == self.logic.Meta.name
        if 'origin' in opts:
            if not is_local or opts['origin'] != 'foreign':
                refp = refplus.logic_link_node(rulecls.Meta.name)
                refp['classes'].append('rule-origin-logic')
                inserts.append(refp)
        if is_local:
            classes.append('rule-origin-local')
        else:
            classes.append('rule-origin-foreign')
        return addnodes.desc('',
            addnodes.desc_signature('', '',
                *inserts,
                addnodes.desc_name(refname, '',
                    nodes.inline(
                        rulecls.name,
                        nametext,
                        classes=['ruledoc', 'rule-sig']),
                    viewcode_anchor(
                        refdomain=domain,
                        reftype=objtype, 
                        refdoc=self.env.docname,
                        refid=refid,
                        reftarget=self.viewcode_target(rulecls),
                        classes=['ruledoc']),
                    classes=['pre', 'ruledoc', 'rule-sig']),
                ids=[nodeid],
                classes=['ruledoc']),
            domain=domain,
            objtype=objtype,
            classes=classes,
            **{'data-rule-origin-logic': rulecls.Meta.name})

    def getnodes_rule_legend(self, rulecls: type[Rule]):
        lw = self.lwuni
        strings = lw.strings
        for name, value in rulecls.legend:
            if lw.canwrite(value):
                text = lw(value)
            else:
                if isinstance(value, tuple):
                    args = name, *value
                else:
                    if name != Marking.tableau:
                        args = Marking.tableau, name, value
                    else:
                        args = name, value
                try:
                    text = strings[*args]
                except KeyError:
                    raise self.error(
                        f'Unwriteable legend item: {(name, value)}'
                        f'for {rulecls}. Tried strings[...] with args {args}')
            yield nodes.inline(text, text, classes=['legend-item', name])

    def getnodes_trunk_prolog(self):
        # Plain docutils nodes, not raw html.
        yield nodes.inline(text='To build the trunk for the argument ')
        notn = self.options['wnotn']
        argnode = nodes.inline(classes=['argument'], notn=notn)
        prem2 = nodez.sentence(sentence = Atomic(0,0), notn=notn)
        prem2 += nodes.subscript('n', 'n')
        argnode += (
            nodez.sentence(sentence=Atomic(0,1), notn=notn),
            nodes.inline(text=' ... '),
            prem2,
            nodes.inline(text=' ∴ '),
            nodez.sentence(sentence=Atomic(1, 0), notn=notn))
        yield argnode
        yield nodes.inline(text=' write:')

    def _check_options_mode(self) -> Literal['argument','rule','build-trunk']:
        opts = self.options
        for mode, names in self.modes.items():
            if mode in opts:
                break
        else:
            if 'argument' in opts:
                badopts = {'conclusion', 'premises'} & set(opts)
                if badopts:
                    raise self.error(f"Option(s) not allowed with 'argument': {badopts}")
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
            :group: operator
            :legend:
            :title: Operator Rules
            :titles:
            :exclude: MaterialConditional, Conditional
    """
    optional_arguments = sys.maxsize

    # Top-level group. Can be subgrouped by individual operator, quantifier, or predicate
    group_choices = {'closure', 'operator', 'quantifier', 'predicate', 'ungrouped'}
    # can be used in 'include' and 'exclude' options
    special_names = {
        'native',
        'non_native',
        'modal',
        'non_modal'}

    option_spec = dict(
        # Common
        logic   = logics.registry,
        format  = optspecs.choice(writers.registry),
        wnotn   = Notation,
        classes = optspecs.classes,

        group = optspecs.choice(group_choices),

        title  = optspecs.string,
        titles = optspecs.choice({'symbols', 'names', 'labels'}, default = 'symbols'),
        flat   = optspecs.flag,

        exclude  = optspecs.idnames,
        include  = optspecs.idnames,
        legend   = optspecs.flag,
        captions = optspecs.flag,
        docflags = optspecs.flag,
        doc      = optspecs.flag)

    groupmode: Literal['group', 'subgroups']
    # Either group or subgroups will be set, but not both.
    group: list[type[Rule]]
    subgroups: dict[Operator|Predicate|Quantifier, list[type[Rule]]]

    default_docflags = ('title', 'titles', 'legend', 'doc')

    title: str|None
    exclude: set[str]
    include: set[str]
    groupid: str

    ruleinfo_cache = {}

    def setup(self):
        """
        only options relevant for super are rule, title, doc
        """
        if self._setup:
            return
        super().setup()
        opts = self.options
        if 'docflags' in opts:
            for name in self.default_docflags:
                opts.setdefault(name, None)
            opts.setdefault('origin', 'foreign')
        label = f"{opts['group'].capitalize()} Rules"
        if 'title' in opts and opts['title'] != '-':
            self.title = opts['title'] or label
        else:
            self.title = None
        self.groupid = inflect.dashcase(self.title or label)
        self.exclude = set(opts.get('exclude', EMPTY_SET))
        self.include = set(opts.get('include', EMPTY_SET))
        self.resolve_special_names()
        try:
            ruleinfo = self.ruleinfo_cache[self.logic]
        except KeyError:
            ruleinfo = self.ruleinfo_cache.setdefault(self.logic, rules_sorted(self.logic))
        group: list[type[Rule]] = ruleinfo['legend_groups'][opts['group']]
        subgroups = ruleinfo['legend_subgroups'].get(opts['group'])
        if not subgroups or 'flat' in opts or opts['group'] == 'ungrouped':
            self.groupmode = 'group'
            self.group = group
        else:
            self.groupmode = 'subgroups'
            self.subgroups = subgroups

    def run(self):
        self.setup()
        assert self.groupmode in ('subgroups', 'group')
        if self.title:
            nodecls = nodes.section
        else:
            nodecls = nodes.container
        cont = nodecls(
            classes=self.options['classes'],
            ids=[self.groupid])
        if self.title:
            cont += nodes.title(text=self.title)
        if self.groupmode == 'subgroups':
            cont += self.get_nodes_subgroups_mode()
        else:
            cont += self.get_nodes_group_mode()
        return [cont]

    def get_nodes_group_mode(self):
        opts = self.options
        opts['classes'].add('tableau-rule-group')
        for rule in self.filter_by_name(self.group):
            opts['rule'] = rule.name
            if 'captions' in opts:
                opts['caption'] = inflect.snakespace(rule.name)
            else:
                opts.pop('caption', None)
            yield from super().run()

    def get_nodes_subgroups_mode(self):
        opts = self.options
        for obj in self.filter_by_name(self.subgroups):
            subgroup = self.subgroups[obj]
            node = nodes.section(
                classes = ['tableau-rule-subgroup'],
                ids = [f'{obj.name.lower()}-rules'])
            if 'titles' in opts:
                titles = opts['titles']
                if titles == 'labels':
                    prefix = getattr(obj, 'label', obj.name)
                elif titles == 'names':
                    prefix = obj.name
                else:
                    prefix = self.lwuni(obj)
                node += nodes.title(text = f'{prefix} Rules')
            for rule in self.exclude_by_name(subgroup):
                opts['rule'] = rule.name
                if 'captions' in opts:
                    opts['caption'] = inflect.snakespace(rule.name)
                else:
                    opts.pop('caption', None)
                node += super().run()
            yield node

    def filter_by_name(self, it: Iterable[_T]) -> Iterator[_T]:
        it = self.exclude_by_name(it)
        if not self.include:
            return it
        return (obj for obj in it if obj.name in self.include)

    def exclude_by_name(self, it: Iterable[_T]) -> Iterator[_T]:
        return (obj for obj in it if obj.name not in self.exclude)

    def resolve_special_names(self):
        for optset in (self.include, self.exclude):
            for name in optset & self.special_names:
                optset.remove(name)
                optset.update(self.get_special_name_values(name))

    def get_special_name_values(self, name: str) -> Iterator[str]:
        if name in ('native', 'non_native'):
            base = self.logic.Meta.native_operators
        elif name in ('modal', 'non_modal'):
            base = self.logic.Meta.modal_operators
        else:
            return
        if name.startswith('non_'):
            base = set(Operator).difference(base)
        yield from (obj.name for obj in base)

    def _check_options_mode(self) -> Literal['rule']:
        if 'group' not in self.options:
            raise self.error(f"Missing required option: group")
        return 'rule'


class TruthTables(BaseDirective, RenderMixin, LogicOptionMixin):
    'Truth tables (raw html).'

    option_spec = dict(
        logic = logics.registry,
        operators = optspecs.opers,
        exclude = optspecs.idnames,
        include = optspecs.idnames,
        wnotn = Notation,
        template = optspecs.string,
        reverse = optspecs.bool_true,
        clear = optspecs.bool_true,
        classes = optspecs.classes)

    special_names = {'native', 'non_native'}

    def run(self):
        classes = self.set_classes()
        opts = self.options
        conf = self.config

        self.exclude = set(opts.get('exclude', EMPTY_SET))
        self.include = set(opts.get('include', EMPTY_SET))
        self.resolve_special_names()

        model = self.logic.Model()
        opers = opts.get('operators')
        if opers is None:
            opers = sorted(self.logic.Meta.truth_functional_operators)
        opers = self.filter_by_name(opers)

        wnotn = opts.get('wnotn', conf[ConfKey.wnotn])
        lw = LexWriter(wnotn, 'html')

        template = opts.get('template', conf[ConfKey.truth_table_template])
        reverse = opts.get('reverse', conf[ConfKey.truth_table_reverse])
        clear = opts.get('clear', True)

        tables = (
            model.truth_table(oper, reverse = reverse)
            for oper in opers)
        context = dict(lw = lw, classes = classes)
        renders = (
            self.render(template, context, table = table)
            for table in tables)
        content = '\n'.join(renders)

        nlist = [nodes.raw(format='html', text=content)]
        if clear:
            nlist.append(block(classes=['clear']))

        return nlist

    def filter_by_name(self, it: Iterable[_T]) -> Iterator[_T]:
        it = self.exclude_by_name(it)
        if not self.include:
            return it
        return (obj for obj in it if obj.name in self.include)

    def exclude_by_name(self, it: Iterable[_T]) -> Iterator[_T]:
        return (obj for obj in it if obj.name not in self.exclude)

    def resolve_special_names(self):
        for optset in (self.include, self.exclude):
            for name in optset & self.special_names:
                optset.remove(name)
                optset.update(self.get_special_name_values(name))

    def get_special_name_values(self, name: str) -> Iterator[str]:
        if name not in ('native', 'non_native'):
            return
        base = self.logic.Meta.native_operators
        if name.startswith('non_'):
            base = set(Operator).difference(base)
        yield from (obj.name for obj in base)


class CSVTable(sphinx.directives.patches.CSVTable, BaseDirective):
    "Override csv-table to allow generator function."

    generator: TableGenerator|None
    option_spec = dict(sphinx.directives.patches.CSVTable.option_spec) | {
        'generator'      : table_generators.__getitem__,
        'generator-args' : optspecs.string,
        'classes'        : optspecs.classes}

    option_spec.pop('class', None)

    def run(self):
        classes = self.set_classes()
        opts = self.options
        if (generator := opts.get('generator')) is None:
            self.generator = None
        else:
            self.generator = generator(self, opts.get('generator-args'))
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
        self.state_machine = self.StateMachineProxy()
        proxy = self.state_machine
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
    app.add_config_value(ConfKey.wfmt, None, 'env', [str])
    app.add_config_value(ConfKey.strings, None, 'env', [str])
    app.add_config_value(ConfKey.truth_table_template, 'truth_table.jinja2', 'env', [str])
    app.add_config_value(ConfKey.truth_table_reverse, True, 'env', [bool])

    app.add_event(SphinxEvent.IncludeRead)
    app.add_directive('include',   Include, override = True)
    app.add_directive('csv-table', CSVTable, override = True)
    app.add_directive('tableau', TableauDirective)
    app.add_directive('tableau-rules', RuleGroupDirective)
    app.add_directive('truth-tables', TruthTables)
    app.add_directive('sentence', SentenceBlock)
