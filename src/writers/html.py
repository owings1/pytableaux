# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
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
# pytableaux - HTML Writer

name = 'HTML'

import logic
from jinja2 import Environment, PackageLoader

class Writer(logic.TableauxSystem.Writer):

    name = name

    env = Environment(
        loader = PackageLoader('writers', 'templates'),
        trim_blocks = True,
        lstrip_blocks = True
    )
    template = env.get_template('structure.html')
    header   = env.get_template('header.html')

    def document_header(self):
        return self.header.render()

    def write(self, tableau, notation, symbol_set=None):
        return self.template.render({
            'tableau'    : tableau,
            'notation'   : notation,
            'symbol_set' : symbol_set
        })