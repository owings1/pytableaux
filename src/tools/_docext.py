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
#
# pytableaux - docutils/sphins exentions.
from __future__ import annotations
import traceback

__all__ = (
    'LexwriteRole',
    'include_directive'
)

import examples
from lexicals import LexType, LexWriter, Notation, Parser, Predicate
from tools.abcs import MapProxy, abstract, AbcMeta

from docutils import nodes
from html import unescape as htmlun
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxRole
import re

logger = logging.getLogger(__name__)


def include_directive(app: Sphinx):
    "Override include directive that allows the app to modify content via events."

    app.add_event('include-read')

    from sphinx.directives.other import Include as BaseInclude

    class Include(BaseInclude):

        def parse(self, text: str, doc):
            lines = text.split('\n')
            source = doc.attributes['source']
            app.emit('include-read', lines)
            self.state_machine.insert_input(lines, source)

        def run(self):
            self.options['parser'] = lambda: self
            super().run()
            return []

    return Include


class BaseRole(SphinxRole, metaclass = AbcMeta):

    @abstract
    def role(self): ...

    def run(self):
        try:
            ret = self.role()
        except:
            logger.error(
                f"rawtext={repr(self.rawtext)}, "
                f"content={self.content}"
            )
            logger.info('Printing traceback')
            traceback.print_exc()
            raise
        else:
            if isinstance(ret, nodes.Node):
                ret = [ret], []
            elif not isinstance(ret, tuple):
                ret = ret, []
            return ret

class LexwriteRole(BaseRole):

    _defaults = MapProxy(dict(
        write_notation   = Notation.standard,
        parse_notation   = Notation.standard,
        preds            = examples.preds,
    ))

    _ctypes = dict(
        valued = {
            LexType.Operator,
            LexType.Quantifier,
            Predicate.System
        }
    )
    _ctypes['nosent'] = _ctypes['valued'] | {
        LexType.Constant,
        LexType.Variable,
        LexType.Predicate,
    }

    
    parser: Parser
    lwhtml: LexWriter

    def __init__(self, **opts):
        opts = dict(self._defaults) | opts
        self.parser = Parser(opts['parse_notation'], opts['preds'])
        self.lwhtml = LexWriter(opts['write_notation'], 'html')

    def role(self):

        text = self.text

        classes = ['lexitem']

        item = None
        match = re.match(r'^(.)([0-9]*)$', text)

        if match:
            char, sub = match.groups()
            table = self.parser.table
            ctype = table.type(char)
            _ctypes = self._ctypes
            if ctype in _ctypes['nosent']:
                # Non-sentence items.
                sub = int(sub) if len(sub) else 0
                if ctype in _ctypes['valued']:
                    item = table.value(char)
                elif ctype is LexType.Predicate:
                    preds = self.parser.preds
                    item = preds.get((table.value(char), sub))
                else:
                    item = ctype.cls(table.value(char), sub)

        if item is None:
            # Parse as sentence.
            item = self.parser(text)

        classes.append(item.TYPE.name.lower())
        rend = htmlun(self.lwhtml(item))

        return nodes.inline(text = rend, classes = classes)

class MetawriteRole(BaseRole):

    _defaults = MapProxy(dict(

    ))

    modes = dict(
        logic_name = dict(
            match = {
                r'^(?:(?P<main>B|G|K|L|Ł|P|RM)(?P<down>3))$' : ('subber',),
                r'^(?:(?P<main>B)(?P<up>3)(?P<down>E))$'  : ('subsup',),
                r'^(?:(?P<main>K)(?P<up>3)(?P<down>WQ?))$': ('subsup',),
                # r'^(?P<name>(?P<main>B|K)(?P<up>3)(?P<down>E|WQ?))$': 'subsup',
                #{'B3E', 'K3W', 'K3WQ'},
                # r'^(B|K)3E|3(?P<down>WQ?)$': 'subsup',
            },
            nodecls = nodes.inline,
            nodecls_map = dict(
                main= nodes.inline,
                up  = nodes.superscript,
                down= nodes.subscript
            ),
        ),
        truth_value = dict(
            nodecls = nodes.strong,
        ),
        # Regex rewrite.
        rewrite = {
            r'^(?:([a-zA-Z])-)?ntuple$': dict(
                rep = lambda m, a = 'a': (
                    f'\\langle {m[1] or a}_0'
                    ', ... ,'
                    f'{m[1] or a}_n\\rangle'
                ),
                classes = ('tuple', 'ntuple'),
                nodecls = nodes.math,
            ),
            r'^(w)([0-9]+)$': dict(
                rep = r'\1_\2',
                classes = ('modal', 'world'),
                nodecls = nodes.math,
            ),
        },
    )
    generic = dict(
        # Math symbol replace.
        math_symbols = {
            r'<': re.escape('\\langle '),
            r'>': re.escape('\\rangle'),
        }
    )
    prefixes = {
        'L': 'logic_name',
        'V': 'truth_value',
        '!': 'rewrite',
    }
    patterns = dict(
        prefixed = r'(?P<raw>(?P<prefix>[%s]){(?P<value>.*?)})' % (
            re.escape(''.join(prefixes.keys()))
        ),
    )
    patterns.update(
        prefixed_role = '^%s$' % patterns['prefixed']
    )

    def __init__(self, **opts):
        opts = dict(self._defaults) | opts

    def role(self):
        text = self.text

        classes = ['metawrite']

        match = re.match(self.patterns['prefixed_role'], text)

        if not match:

            # Try rewrite.
            mode = 'rewrite'
            for pat, info in self.modes[mode].items():
                rend, num = re.subn(pat, info['rep'], text)
                if num:
                    classes.extend(info['classes'])
                    nodecls = info['nodecls']
                    break
            else:
                # Generic math symbols.
                mode = 'math_symbols'
                nodecls = nodes.math
                if 'w' in text:
                    classes.append('modal')
                if '<' in text and '>' in text:
                    classes.append('tuple')
                rend = text
                for pat, rep in self.generic[mode].items():
                    rend = re.sub(pat, rep, rend)
                logger.info((text,rend))

            classes.append(mode)
            return nodecls(text = rend, classes = classes)

        matchd = match.groupdict()
        mode: str = self.prefixes[matchd['prefix']]
        value: str = matchd['value']
        moded: dict = self.modes[mode]

        classes.append(mode)

        if mode == 'rewrite':
            for pat, info in moded.items():
                rend, num = re.subn(pat, info['rep'], value)
                if num:
                    break
            else:
                logger.error(f'No {mode} match for {repr(value)}')
            classes.extend(info['classes'])
            nodecls = info['nodecls']
            return nodecls(text = rend, classes = classes)

        if mode == 'truth_value':
            rend = value
            nodecls = moded['nodecls']
            return nodecls(text = rend, classes = classes)

        if mode == 'logic_name':

            for pat, addcls in moded['match'].items():
                m = re.match(pat, value)
                if not m:
                    continue
                md = m.groupdict()
                classes.extend(addcls)
                nodecls_map: dict = moded['nodecls_map']
                return [
                    nodecls(text = md[key], classes = classes + [key])
                    for key, nodecls in nodecls_map.items()
                    if key in md
                ]
            
            rend = value
            nodecls = moded['nodecls']
            return nodecls(text = rend, classes = classes)