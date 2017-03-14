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
# pytableaux - ASCII writer
#

name = "ASCII"

def write(tableau, notation):
    return write_structure(tableau.tree, notation)
    
def write_structure(structure, notation, indent=0):
    node_strs = []
    for node in structure['nodes']:
        s = ''
        if 'sentence' in node.props:
            s += notation.write(node.props['sentence'])
            if 'world' in node.props:
                s += ', w' + str(node.props['world'])
        if 'designated' in node.props:
            if node.props['designated']:
                s += ' +'
            else:
                s += ' -'
        if 'world1' in node.props and 'world2' in node.props:
            s += 'w' + str(node.props['world1']) + 'R' + 'w' + str(node.props['world2'])
        if node.ticked:
            s += ' *'
        node_strs.append(s)
    s = ' ' * indent + ' | '.join(node_strs)
    if structure['closed']:
        s += ' (X)'
    i = len(s) + 1
    for child in structure['children']:
        s += "\n" + write_structure(child, notation, i)
    return s