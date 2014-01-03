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