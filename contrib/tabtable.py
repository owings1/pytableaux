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
Prints tableau results table.

Requires table-packages dependencies.
"""
from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType as MapProxy
from typing import Sequence

from tabulate import tabulate, tabulate_formats

from pytableaux.examples import arguments as arguments
from pytableaux.lang import Argument
from pytableaux.logics import LogicSet, LogicType, registry
from pytableaux.proof import Tableau
from pytableaux.tools import MapCover

from . import readlist

logger = logging.getLogger('tabtable')

@dataclass(kw_only=True, slots=True)
class Options:
    logics: tuple[LogicType, ...]
    arguments: tuple[Argument, ...]
    format: str
    limit: int|None
    summary_only: bool
    order: Sequence[tuple[str, bool]]
    columns: Sequence[str]

def parser():
    parser = ArgumentParser(description='Prints tableau results table')
    arg = parser.add_argument
    arg(
        '--logics', '--logic', '-l',
        type=logicopt,
        default=tuple(sorted(registry.all())),
        help=(
            'Comma-separated logics to generate, default is all. '
            'To specify an exclusion list, prefix the option with ^.'))
    arg(
        '--arguments', '--argument', '-a',
        type=lambda opt: tuple(Argument(arguments.get(a, a)) for a in readlist(opt)),
        default=arguments.values(),
        help='Comma-separated arguments to generate, default is all. Can be example name or argstr.')
    arg(
        '--format',
        choices=tabulate_formats,
        default='simple',
        help='The tabulate format, default is simple')
    arg(
        '--limit',
        type=int,
        default=None,
        help='The limit of results to display')
    arg(
        '--order', '-o',
        type=orderopt,
        default=ORDERINGS[':benchmark'],
        help='Column ordering'),
    arg('--columns', '-c',
        type=lambda opt: tuple(Row.FIELDS[Row.FIELDS.index(col)] for col in readlist(opt)),
        default=Row.FIELDS,
        help='Columns to display, default: ' + ','.join(Row.FIELDS))
    arg(
        '--summary-only', '-s',
        dest='summary_only',
        action='store_true',
        help='Only display the summary')
    return parser

ORDERINGS = {
    ':benchmark': (
        ('branches', True),
        ('nodes', True),
        ('logic', False),
        ('argument', False))}

class Row(MapCover):

    FIELDS = (
        'logic',
        'argument',
        'valid',
        'steps',
        'branches',
        'nodes')
    SUMMABLE = (
        'steps',
        'nodes',
        'branches')

    sortkeys: Mapping

    __slots__ = ('sortkeys')

    def __init__(self, tab: Tableau):
        super().__init__(dict(
            logic = tab.logic.Meta.name,
            argument = tab.argument.title or tab.argument.argstr(),
            valid = 'NY'[tab.valid],
            steps = len(tab.history),
            branches = len(tab),
            nodes = tab.tree.distinct_nodes))
        self.sortkeys = MapProxy(dict(self,
            valid = tab.valid,
            logic = tab.logic.Meta))

class Builder:

    def __init__(self, opts: Options):
        self.opts = opts

    def build(self):
        opts = self.opts
        logger.info(
            f'Building {len(opts.arguments) * len(opts.logics)} tableaux')
        self.rows = rows = [
            Row(Tableau(logic, argument).build())
            for logic in opts.logics for argument in opts.arguments]
        for field, reverse in reversed(opts.order):
            rows.sort(key=lambda row: row.sortkeys[field], reverse=reverse)
        if opts.limit is not None:
            del rows[opts.limit:]
        return self

    def table(self):
        head = {name: name.title() for name in self.opts.columns}
        return tabulate(self.rows, head, tablefmt=self.opts.format)

    def summary(self):
        return tabulate(
            ((name.title(), value) for name, value in self.totals().items()),
            ('Totals', ''),
            tablefmt=self.opts.format)

    def totals(self):
        return {
            name: sum(row[name] for row in self.rows)
            for name in Row.SUMMABLE}

def main(*args):
    opts = Options(**vars(parser().parse_args(args)))
    logging.basicConfig(level=logging.INFO)
    builder = Builder(opts).build()
    if not opts.summary_only:
        print(builder.table())
    print(builder.summary())

def logicopt(s: str):
    logics = LogicSet()
    exclude = s[0] == '^'
    if exclude:
        logics |= registry.all()
        logics -= readlist(s[1:])
    else:
        logics |= readlist(s)
    return logics

def orderopt(s: str):
    fields = set(Row.FIELDS)
    order = []
    revmap = {'asc': False, 'desc': True}
    for opt in readlist(s):
        if opt in ORDERINGS:
            order.extend(ORDERINGS[opt])
            continue
        parts = iter(opt.split('__', 1))
        field = next(parts)
        if field not in fields:
            raise ValueError(f'{field=}')
        try:
            direction = next(parts)
        except StopIteration:
            direction = 'asc'
        try:
            reverse = revmap[direction.lower()]
        except KeyError:
            raise ValueError(f'{direction=}')
        order.append((field, reverse))
    return order

if __name__ == '__main__':
    main(*sys.argv[1:])
