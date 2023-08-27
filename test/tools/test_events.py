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
# pytableaux.tools.events tests
from pytableaux.tools.events import *

from ..utils import BaseCase as Base


class TestListeners(Base):

    def test_once_listener(self):
        e = EventsListeners()
        e.create('test')
        def cb(): pass
        e.once('test', cb)
        self.assertEqual(len(e['test']), 1)
        self.assertIn(cb, e['test'])
        e.emit('test')
        self.assertEqual(len(e['test']), 0)

    def test_off(self):
        def cb(): pass
        e = EventsListeners()
        e.create('test')
        e.on('test', cb)
        self.assertIn(cb, e['test'])
        e.off('test', cb)
        self.assertEqual(len(e['test']), 0)
