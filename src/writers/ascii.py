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
import logic

name = "ASCII"

HCHAR = '|'
VCHAR = '_'
TCHAR = '-'

class Writer(logic.TableauxSystem.Writer):

    name = name

    def write_tableau(self, tableau, writer, opts):
        s = ''
        if 'status_panel' in opts and opts['status_panel']:
            s += self.write_status(tableau, writer, opts)
            s += '\n\n'
        s += '\n'.join([
            'Proof',
            '=====',
            ''
        ])
        s += self.write_structure(tableau.tree, writer, opts)
        return s

    def write_structure(self, structure, writer, opts, indent = 0, indents=[]):
        node_strs = []
        for node in structure['nodes']:
            s = ''
            if 'sentence' in node.props:
                s += writer.write(node.props['sentence'], drop_parens = True)
                if 'world' in node.props and node.props['world'] != None:
                    s += ', w' + str(node.props['world'])
            if 'designated' in node.props and node.props['designated'] != None:
                if node.props['designated']:
                    s += ' +'
                else:
                    s += ' -'
            if 'world1' in node.props and 'world2' in node.props:
                s += 'w' + str(node.props['world1']) + 'R' + 'w' + str(node.props['world2'])
            if node.ticked:
                s += ' *'
            node_strs.append(s)
        s = ''
        for ind in indents:
            s += ' ' * (ind - 1) + HCHAR
        if indent > 0:
            s += 2 * VCHAR + ' '
        s += ' | '.join(node_strs)
        if structure['closed']:
            s += ' (X)'
        elif len(structure['children']) > 0:
            s += ' ' + HCHAR
        i = len(s)
        for child in structure['children']:
            inds = list(indents)
            inds.append(i - indent)
            s += "\n" + self.write_structure(child, writer, opts, indent = i, indents=inds)
            s += '\n'
            for ind in inds:
                s += ' ' * (ind - 1) + HCHAR
        return s

    def write_status(self, tableau, writer, opts):
        lines = []
        if tableau.argument != None:
            lines += [
                'Argument',
                '========'
            ]
            pstrs = [writer.write(premise, drop_parens=True) for premise in tableau.argument.premises]
            cstr = writer.write(tableau.argument.conclusion, drop_parens=True)
            lines += pstrs
            if len(tableau.argument.premises):
                lines.append(TCHAR * min(max([len(s) for s in pstrs] + [5, len(cstr)]), 20))
            lines.append(cstr)
            lines.append('')
        result = 'Valid' if tableau.valid else 'Invalid'
        lines += [
            'Summary',
            '======='
        ]
        
        lines += [
            'Logic          : {0} - {1}'.format(tableau.logic.name, tableau.logic.description),
            'Result         : {0}'.format(tableau.stats['result']),
            'Branches       : {0}'.format(tableau.stats['branches'])
        ]
        if not tableau.valid:
            lines += [
                'Open Branches  : {0}'.format(tableau.stats['open_branches'])
            ]
        lines += [
            'Distinct Nodes : {0}'.format(tableau.stats['distinct_nodes']),
            'Rules Applied  : {0}'.format(tableau.stats['rules_applied'])
        ]
        return '\n'.join(lines)