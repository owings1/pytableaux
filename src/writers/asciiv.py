# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - ASCII-V writer

# this is a work in progress
#
# [a, b, c, d, e, f] X
# [a, d, c] X
# [a, b, c, d, a]
# 
# 
#   d - c (X)
#  /
# a           e - f (X)
#  \         /
#   b - c - d
#            \ 
#             a
#             
# 
# 
# --------------------
#          e - f - a
#         /
#    d - c
#   /     \ 
#  /       f - a - b
# a           
#  \           e - f (X)
#   \         /
#    b - c - d
#             \ 
#              a
#              
# 
# a
#  d - c
#       e - f - a
#       f - a - b
#  b - c - d
#           e - f (X)
#           a

import logic

name = 'ASCII-V'

class Writer(logic.TableauxSystem.Writer):

    def _write_tableau(self, tableau, sw, opts):
        return self.__write_structure(tableau.tree, sw, opts)

    def __write_structure(self, structure, sw, opts, indent = 0):
        node_strs = []
        for node in structure['nodes']:
            s = ''
            if 'sentence' in node.props:
                s += sw.write(node.props['sentence'])
                if 'world' in node.props:
                    s += ', w' + str(node.props['world'])
            if 'designated' in node.props:
                if node.props['designated']:
                    s += ' +'
                else:
                    s += ' -'
            if 'ellipsis' in node.props and node.props['ellipsis']:
                s += '...'
            if node.ticked:
                s += ' *'
            node_strs.append(s)
        s = ' ' * indent + ' | '.join(node_strs)
        if structure['closed']:
            s += ' (X)'
        i = len(s) + 1
        for child in structure['children']:
            s += "\n" + self.__write_structure(child, sw, opts, indent = i)
        return s