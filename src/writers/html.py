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
        return self.env.get_template('header.html').render()
        #return self.header.render()

    def write_tableau(self, tableau, writer, opts):
        if tableau.argument != None:
            premises = [writer.write(premise, drop_parens = True) for premise in tableau.argument.premises]
            conclusion = writer.write(tableau.argument.conclusion, drop_parens = True)
        else:
            premises = None
            conclusion = None
        return self.env.get_template('structure.html').render({
            'tableau'    : tableau,
            'writer'     : writer,
            'opts'       : opts,
            'premises'   : premises,
            'conclusion' : conclusion
        })