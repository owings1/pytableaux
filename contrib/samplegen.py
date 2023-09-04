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
Generate sample tableaux files from argument examples.
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from os import mkdir
from os.path import abspath

from pytableaux import examples
from pytableaux.lang import Notation
from pytableaux.logics import LogicType, registry
from pytableaux.proof import TabWriter
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
    '--logic', '-l',
    type=lambda opt: tuple(map(registry, filter(None, map(str.strip, opt.split(','))))),
    default=(),
    help='Comma-separated logics to generate, default is all')

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
    logic: tuple[LogicType, ...]
    fulldoc: bool
    inline_css: bool

def main(*args):
    opts = Options(**vars(parser.parse_args(args)))
    logging.basicConfig(level=logging.INFO)
    try:
        mkdir(opts.outdir)
    except FileExistsError:
        pass
    pw = TabWriter(
        format=opts.format,
        notation=opts.notation,
        fulldoc=opts.fulldoc,
        inline_css=opts.inline_css)
    for tab in examples.tabiter(*opts.logic):
        name = slug(f'{tab.logic.Meta.name}_{tab.argument.argstr()}')
        outfile = abspath(f'{opts.outdir}/{name}.{pw.format}')
        logger.info(f'writing {outfile}')
        with open(outfile, 'w') as file:
            file.write(pw(tab))

if __name__ == '__main__':
    main(*sys.argv[1:])