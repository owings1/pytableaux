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
Generates PDF files for all sample LaTeX files.

No Python dependencies. Designed to run in texlive docker image.
"""
from __future__ import annotations

import argparse
import logging
import os
import os.path
import subprocess
import sys
from collections import deque
from dataclasses import dataclass
from itertools import filterfalse
from typing import Mapping

from . import make_queue_workers, resolve_srcfiles

MAX_THREADS = max(1, min(4, os.cpu_count()))

logger = logging.getLogger('pdfgen')

@dataclass(kw_only=True, slots=True)
class Options:
    srcdir: str
    outdir: str|None
    incremental: bool
    threads: int
    clean: bool

def parser():
    parser = argparse.ArgumentParser(
        description='Generate PDF files from latex files')

    arg = parser.add_argument
    arg(
        '--srcdir', '-s',
        type=os.path.abspath,
        required=True,
        help='The source directory')
    arg(
        '--outdir', '-o',
        type=os.path.abspath,
        default=None,
        help='The output directory, default is srcdir')
    arg(
        '--incremental', '-i',
        action='store_true',
        help='Skip existing pdf files')
    arg(
        '--threads', '-t',
        type=lambda opt: min(MAX_THREADS, int(opt)),
        default=1,
        help=f'The number of threads to use, default is 1 (max {MAX_THREADS})')
    arg(
        '--noclean',
        action='store_false',
        dest='clean',
        help='Do not clean .log and .aux files')
    return parser

def main(*args):
    opts = Options(**vars(parser().parse_args(args)))
    logging.basicConfig(level=logging.INFO)
    if opts.outdir is None:
        opts.outdir = opts.srcdir
    else:
        try:
            os.mkdir(opts.outdir)
        except FileExistsError:
            pass
    files = resolve_srcfiles(
        srcdir=opts.srcdir,
        srcext='tex',
        outdir=opts.outdir,
        outext='pdf',
        incremental=opts.incremental)
    if not len(files):
        logger.warning(f'No files to process')
        return
    logger.info(f'Processing {len(files)} files')
    queue = deque(files)
    workers = make_queue_workers(queue, opts.threads, runner, files, opts)
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()


def runner(file: str, files: Mapping[str, str], opts: Options):
    outbase = '.'.join(files[file].split('.')[:-1])
    auxfiles = tuple(filterfalse(os.path.exists, (
        f'{outbase}.{ext}' for ext in ('aux', 'log'))))
    args = (
        'latex',
        '-interaction=nonstopmode',
        '-halt-on-error',
        '-output-directory',
        opts.outdir,
        '-output-format=pdf',
        file)
    proc: subprocess.CompletedProcess = subprocess.run(args,
        capture_output=True,
        text=True,
        timeout=60)
    try:
        proc.check_returncode()
    except:
        logger.error(proc.stdout)
        logger.error(proc.stderr)
        raise
    for file in auxfiles:
        try:
            os.unlink(file)
        except FileNotFoundError:
            pass

if __name__ == '__main__':
    main(*sys.argv[1:])