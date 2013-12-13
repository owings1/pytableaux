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
        if node.ticked:
            s += ' *'
        node_strs.append(s)
    s = ' ' * indent + ' | '.join(node_strs)
    if structure['closed']:
        s += ' (X)'
    i = len(s) + 1
    for child in structure['children']:
        s += "\n" + self.write_structure(child, notation, i)
    return s