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
Generates LaTeX files for all example arguments and all logics.
"""
from __future__ import annotations

import sys
from os import mkdir
from os.path import abspath

from pytableaux import examples
from pytableaux.proof import TabWriter
from pytableaux.tools.inflect import slug


def main(outdir: str):
    outdir = abspath(outdir)
    try:
        mkdir(outdir)
    except FileExistsError:
        pass
    pw = TabWriter(format='latex', notation='standard')
    for tab in examples.tabiter():
        name = slug(f'{tab.logic.Meta.name}_{tab.argument.argstr()}')
        outfile = abspath(f'{outdir}/{name}.{pw.format}')
        print(f'writing {outfile}')
        with open(outfile, 'w') as file:
            file.write(pw(tab, fulldoc=True))

if __name__ == '__main__':
    main(*sys.argv[1:])