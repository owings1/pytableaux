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
Generate sample tableaux files from examples.
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from os import mkdir
from os.path import abspath

from pytableaux.examples import args as examples
from pytableaux.lang import Argument, Notation
from pytableaux.logics import LogicType, registry
from pytableaux.proof import Tableau, TabWriter
from pytableaux.tools.inflect import slug

logger = logging.getLogger('samplegen')

parser = argparse.ArgumentParser(
    description='Generate sample tableaux files')

arg = parser.add_argument
arg(
    '--outdir', '-o',
    type=abspath,
    required=True,
    help='The output directory')

arg(
    '--format', '-f',
    type=str,
    default='latex',
    help='The output format, default is latex')

arg(
    '--notation', '-n',
    type=Notation,
    default=Notation.standard,
    help='The output notation, default is standard')

arg(
    '--logic', '--logics', '-l',
    dest='logics',
    type=lambda opt: tuple(map(registry, readlist(opt))),
    default=tuple(sorted(registry.all())),
    help='Comma-separated logics to generate, default is all')

arg(
    '--argument', '--arguments', '-a',
    dest='arguments',
    type=lambda opt: tuple(Argument(examples.get(a, a)) for a in readlist(opt)),
    default=examples.values(),
    help='Comma-separated arguments to generate, default is all. Can be example name or argstr.')

arg(
    '--nodoc',
    action='store_false',
    dest='fulldoc',
    help='Skip doc header/footer')

arg(
    '--inline-css',
    action='store_true',
    help='Include inline css (HTML only)')

@dataclass(kw_only=True, slots=True)
class Options:
    outdir: str
    format: str
    notation: Notation
    logics: tuple[LogicType, ...]
    arguments: tuple[Argument, ...]
    fulldoc: bool
    inline_css: bool

def main(*args):
    opts = Options(**vars(parser.parse_args(args)))
    logging.basicConfig(level=logging.INFO)
    try:
        mkdir(opts.outdir)
    except FileExistsError:
        pass
    pw = TabWriter(**{name: getattr(opts, name) for name in (
        'format',
        'notation',
        'fulldoc',
        'inline_css')})
    ext = pw.file_extension
    outdir = opts.outdir
    for logic in map(registry, opts.logics):
        for argument in opts.arguments:
            tab = Tableau(logic=logic, argument=argument).build()
            name = slug(f'{logic.Meta.name}_{argument.argstr()}')
            file = abspath(f'{outdir}/{name}.{ext}')
            logger.info(f'writing {file}')
            with open(file, 'w') as file:
                file.write(pw(tab))

def readlist(s: str, /, *, sep=','):
    return filter(None, map(str.strip, s.split(sep)))

if __name__ == '__main__':
    main(*sys.argv[1:])