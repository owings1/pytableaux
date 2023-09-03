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
Generates cropped image files for all sample PDF files.

Requires img-packages dependencies.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import threading
import traceback
from collections import deque
from os.path import abspath, basename
from typing import Callable, Iterable

from pdf2image import convert_from_path

from . import autocrop

MAX_THREADS = max(1, int(os.cpu_count() // 1.2))

pat_file = re.compile(r'.*\.pdf$')

def makeimg(srcfile: str, tmpdir: tempfile.TemporaryDirectory, outdir: str, ext: str):
    outparts = basename(srcfile).split('.')
    outparts.pop()
    ext = ext.strip('.')
    outname = '.'.join(outparts) + f'.{ext}'
    outfile = abspath(f'{outdir}/{outname}')
    images = convert_from_path(srcfile, output_folder=tmpdir, grayscale=True)
    if len(images) != 1:
        print(f'WARNING: Skipping {srcfile}: got {len(images)} pages, expecting 1')
        return
    image, = images
    autocrop.autocrop(image).save(outfile)

def worker(queue: deque[str], func: Callable, *args, **kw):
    while True:
        try:
            item = queue.popleft()
        except IndexError:
            break
        print(f'processing {item}')
        try:
            func(item, *args, **kw)
        except:
            traceback.print_exc()
            print(f'WARNING: failed to process: {item}')

def makeall(srcfiles: Iterable[str], outdir: str, ext: str, threads: int):
    queue = deque(srcfiles)
    threads = min(MAX_THREADS, max(1, threads), len(queue))
    with tempfile.TemporaryDirectory() as tmpdir:
        workers = tuple(
            threading.Thread(
                name=f'Worker-{i + 1}',
                target=worker,
                args=(queue, makeimg, tmpdir, outdir, ext))
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
    makeall(srcfiles=srcfiles, outdir=outdir, ext='jpg', threads=threads)

if __name__ == '__main__':
    main(*sys.argv[1:])