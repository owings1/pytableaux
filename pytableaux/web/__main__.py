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
pytableaux web server
^^^^^^^^^^^^^^^^^^^^^

"""

from __future__ import annotations

__all__ = ()

if  __name__ == '__main__':

    if '.' not in __package__:
        import os.path
        import sys
        addpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )
        if addpath not in sys.path:
            sys.path.insert(1, addpath)

    from .application import WebApp
    WebApp().start()
