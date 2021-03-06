# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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

    def write_tableau(self, tableau, sw, opts):
        if tableau.argument != None:
            premises = [sw.write(premise, drop_parens = True) for premise in tableau.argument.premises]
            conclusion = sw.write(tableau.argument.conclusion, drop_parens = True)
        else:
            premises = None
            conclusion = None
        return self.env.get_template('proof.html').render({
            'tableau'    : tableau,
            'sw'         : sw,
            'opts'       : opts,
            'premises'   : premises,
            'conclusion' : conclusion
        })