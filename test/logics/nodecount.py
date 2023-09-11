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
#
# ------------------
#
# pytableaux.logics.nodecount
from __future__ import annotations

import logging
import operator as opr
import sys
from argparse import ArgumentParser
from dataclasses import dataclass

from tabulate import tabulate, tabulate_formats

from pytableaux.examples import arguments as arguments
from pytableaux.lang import Argument
from pytableaux.logics import LogicSet, LogicType, registry
from pytableaux.proof import Tableau
from pytableaux.tools import membr, wraps

logger = logging.getLogger('nodcount')

@dataclass(kw_only=True, slots=True)
class Options:
    logics: tuple[LogicType, ...]
    arguments: tuple[Argument, ...]
    format: str
    limit: int|None

def parser():
    parser = ArgumentParser(description='Count proof nodes & branches for benchmarking')
    arg = parser.add_argument
    arg(
        '--logic', '--logics', '-l',
        dest='logics',
        type=logicopt,
        default=tuple(sorted(registry.all())),
        help=(
            'Comma-separated logics to generate, default is all. '
            'To specify an exclusion list, prefix the option with ^.'))
    arg(
        '--argument', '--arguments', '-a',
        dest='arguments',
        type=lambda opt: tuple(Argument(arguments.get(a, a)) for a in readlist(opt)),
        default=arguments.values(),
        help='Comma-separated arguments to generate, default is all. Can be example name or argstr.')
    arg(
        '--format',
        dest='format',
        choices=tabulate_formats,
        default='simple',
        help='The tabulate format, default is simple')
    arg(
        '--limit',
        dest='limit',
        type=int,
        default=None,
        help='The limit of results to display')
    return parser

class Builder:

    head = (
        'Logic',
        'Argument',
        'Branches',
        'Nodes')

    def __init__(self, opts: Options):
        self.opts = opts

    def build(self):
        opts = self.opts
        arglen, loglen = map(len, (opts.arguments, opts.logics))
        totallen = arglen * loglen
        logger.info(f'Building {totallen} tableaux')
        self.rows = sorted(
            self.Row(Tableau(logic, argument).build())
            for logic in opts.logics for argument in opts.arguments)
        if opts.limit is not None:
            del self.rows[opts.limit:]
        return self

    def table(self):
        return tabulate(self.rows, self.head, tablefmt=self.opts.format)

    def totals(self):
        return tabulate(
            [
                ['Branches', sum(row.branches for row in self.rows)],
                ['Nodes', sum(row.nodes for row in self.rows)]
            ],
            ['Totals', ''],
            tablefmt=self.opts.format)

    class Row:

        logic: str
        argument: str
        branches: int
        nodes: int

        entry = tuple[str, str, int, int]
        key = tuple[int, int, str, str]

        def __init__(self, tab: Tableau):
            self.logic = tab.logic.Meta.name
            self.argument = tab.argument.title or tab.argument.argstr()
            self.branches = len(tab)
            self.nodes = tab.tree.distinct_nodes
            self.entry = (self.logic, self.argument, self.branches, self.nodes)
            self.key = (-self.branches, -self.nodes, tab.logic.Meta, self.argument)

        @membr.defer
        def wrapper(member: membr):
            @wraps(func := getattr(tuple, member.name))
            def wrapped(self: Builder.Row, *args):
                return func(self.entry, *args)
            return wrapped

        __iter__ = __getitem__ = __len__ = __hash__ = __eq__ = wrapper()

        def __reversed__(self):
            return reversed(self.entry)

        @membr.defer
        def wrapper(member: membr):
            @wraps(oper := getattr(opr, member.name))
            def wrapped(self: Builder.Row, other):
                if isinstance(other, type(self)):
                    return oper(self.key, other.key)
                return NotImplemented
            return wrapped

        __lt__ = __gt__ = __le__ = __ge__ = wrapper()

        del(wrapper)


def main(*args):
    opts = Options(**vars(parser().parse_args(args)))
    logging.basicConfig(level=logging.INFO)
    builder = Builder(opts).build()
    print(builder.table())
    print(builder.totals())

def logicopt(s: str):
    logics = LogicSet()
    exclude = s[0] == '^'
    if exclude:
        logics |= registry.all()
        logics -= readlist(s[1:])
    else:
        logics |= readlist(s)
    return logics

def readlist(s: str, /, *, sep=','):
    return filter(None, map(str.strip, s.split(sep)))

if __name__ == '__main__':
    main(*sys.argv[1:])