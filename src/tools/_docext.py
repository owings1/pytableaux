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
