import os
import sys
import shutil

import click


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
        with open(os.path.join(destination, '__init__.py'), 'w') as f:
            f.write('# generated via cli')

        if not os.path.isfile('README.rst'):
            with open('README.rst', 'w') as f:
                f.write('# generated via cli')

        if not os.path.isfile('setup.py'):
            shutil.move(os.path.join(destination, 'setup.py'), '.')
        else:
            os.remove(os.path.join(destination, 'setup.py'))

    except OSError as e:
        print('Unable to create new app. Error: %s' % str(e), file=sys.stderr)


if __name__ == '__main__':
    cli()
