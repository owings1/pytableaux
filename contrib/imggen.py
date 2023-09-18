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

Requires image-packages dependencies.
"""
from __future__ import annotations

import argparse
import enum
import logging
import os
import sys
import tempfile
from collections import deque
from dataclasses import dataclass
from os.path import abspath
from typing import Mapping

from pdf2image import convert_from_path

from . import autocrop, make_queue_workers, resolve_srcfiles

MAX_THREADS = max(1, min(3, int(os.cpu_count() // 1.2)))

logger = logging.getLogger('pdfgen')

class ImageFormat(str, enum.Enum):
    jpg = 'jpg'
    png = 'png'

@dataclass(kw_only=True, slots=True)
class Options:
    srcdir: str
    outdir: str|None
    incremental: bool
    threads: int
    format: ImageFormat
    crop: bool

def parser():
    parser = argparse.ArgumentParser(
        description='Generate image files from PDF files')

    arg = parser.add_argument
    arg(
        '--srcdir', '-s',
        type=abspath,
        required=True,
        help='The source directory')
    arg(
        '--outdir', '-o',
        type=abspath,
        default=None,
        help='The output directory, default is srcdir')
    arg(
        '--format', '-f',
        type=ImageFormat,
        default=ImageFormat.jpg,
        help=f'The image format, default jpg (options: {", ".join(f.value for f in ImageFormat)})')
    arg(
        '--nocrop',
        action='store_false',
        dest='crop',
        help='Do not crop files')
    arg(
        '--incremental', '-i',
        action='store_true',
        help='Skip existing image files')
    arg(
        '--threads', '-t',
        type=lambda opt: min(MAX_THREADS, int(opt)),
        default=1,
        help=f'The number of threads to use, default is 1 (max {MAX_THREADS})')
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
        srcext='pdf',
        outdir=opts.outdir,
        outext=opts.format.value,
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
    with tempfile.TemporaryDirectory() as tmp:
        images = convert_from_path(file, output_folder=tmp, grayscale=True)
    try:
        image, = images
    except ValueError:
        logger.warning(f'Skipping {file}: got {len(images)} pages, expecting 1')
        return
    if opts.crop:
        image = autocrop(image)
    image.save(files[file])

if __name__ == '__main__':
    main(*sys.argv[1:])
