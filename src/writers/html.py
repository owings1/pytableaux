name = 'HTML'

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('writers', 'templates'), trim_blocks=True, lstrip_blocks=True)
template = env.get_template('structure.html')

def write(tableau, notation):
    return template.render({
        'tableau': tableau,
        'notation': notation
    })