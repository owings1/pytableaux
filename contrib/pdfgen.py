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

import os
import re
import subprocess
import sys
import threading
from collections import deque
from os.path import abspath
from typing import Callable, Iterable

MAX_THREADS = max(1, int(os.cpu_count() * 1.5))

pat_file = re.compile(r'.*\.latex$')

def makepdf(srcfile: str, outdir: str):
    args = (
        'latex',
        '-interaction=nonstopmode',
        '-halt-on-error',
        '-output-directory',
        outdir,
        '-output-format=pdf',
        srcfile)
    subprocess.run(args,
        check=True,
        stderr=sys.stderr,
        stdout=sys.stdout,
        timeout=60)

def worker(queue: deque[str], func: Callable, *args, **kw):
    while True:
        try:
            item = queue.popleft()
        except IndexError:
            break
        func(item, *args, **kw)

def makeall(srcfiles: Iterable[str], outdir: str, threads: int):
    queue = deque(srcfiles)
    threads = min(MAX_THREADS, max(1, threads), len(queue))
    workers = tuple(
        threading.Thread(
            name=f'Worker-{i + 1}',
            target=worker,
            args=(queue, makepdf, outdir))
        for i in range(threads))
    for thread in workers:
        thread.start()
    for thread in workers:
        thread.join()

def main(srcdir: str, outdir: str|None=None):
    srcdir = abspath(srcdir)
    if outdir is None:
        outdir = srcdir
    else:
        outdir = abspath(outdir)
        try:
            os.mkdir(outdir)
        except FileExistsError:
            pass
    threads = int(os.getenv('THREADS') or 1)
    srcfiles = sorted(filter(pat_file.match, os.listdir(srcdir)), key=str.lower)
    srcfiles = list(map(abspath, (f'{srcdir}/{file}' for file in srcfiles)))
    if not len(srcfiles):
        print(f'No files to process')
        return
    print(f'Processing {len(srcfiles)} files')
    makeall(srcfiles=srcfiles, outdir=outdir, threads=threads)

if __name__ == '__main__':
    main(*sys.argv[1:])