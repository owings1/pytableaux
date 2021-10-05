from os import path


__version__ = '2.0.0'

version_info = __version__.split('.')

copyright = '2014-2021, Doug Owings. Released under the GNU Affero General Public License v3 or later'
source_href = 'https://github.com/owings1/pytableaux'
issues_href = 'https://github.com/owings1/pytableaux/issues'
package_dir = path.dirname(path.abspath(__file__))

# compatibility
version = __version__
# lexwriter_encodings = ['html', 'ascii']
# tabwriter_names = ['html', 'text']
