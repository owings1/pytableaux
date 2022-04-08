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
# pytableaux - sphinx extension
from __future__ import annotations

from docutil import Helper

from sphinx.application import Sphinx
import sphinx.config

_helpers  = {}

def gethelper(app: Sphinx) -> Helper:
    return _helpers[app]

def setup(app: Sphinx):
    app.add_config_value('pt_options', {}, 'env', [dict])
    app.connect('config-inited', _init_app)
    app.connect('build-finished', _remove_app)

def _init_app(app: Sphinx, config: sphinx.config.Config):
    opts = config['pt_options']
    _helpers[app] = Helper(**opts)

def _remove_app(app, exception):
    del _helpers[app]