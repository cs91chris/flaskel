import os
import sys
import shutil
from pathlib import Path

import click

INIT_CONTENT = """
# generated via cli
from .version import *
"""


@click.group()
def cli():
    """

    """
    pass


@cli.command(name='init')
@click.argument('name')
def init(name):
    """

    :param name: application name
    """
    import flaskel

    package_path = flaskel.__path__[0]
    source = os.path.join(package_path, 'skeleton')
    destination = name

    try:
        shutil.copytree(source, destination)

        init_file = Path(os.path.join(destination, '__init__.py'))
        init_file.write_text(INIT_CONTENT)

        if not os.path.isfile('setup.py'):
            shutil.move(os.path.join(destination, 'setup.py'), '.')

            setup_file = Path('setup.py')
            text = setup_file.read_text()
            text = text.replace('{skeleton}', name)
            setup_file.write_text(text)
        else:
            os.remove(os.path.join(destination, 'setup.py'))

        cli_file = Path(os.path.join(destination, 'cli.py'))
        text = cli_file.read_text()
        text = text.replace('from .ext', 'from {}.ext'.format(name))
        text = text.replace('from .blueprint', 'from {}.blueprint'.format(name))
        cli_file.write_text(text)
    except OSError as e:
        print('Unable to create new app. Error: %s' % str(e), file=sys.stderr)


if __name__ == '__main__':
    cli()
