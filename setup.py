"""
Flaskel
-------
"""
import os
import re
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test

package = 'flaskel'
skeleton = 'skeleton'
BASE_PATH = os.path.dirname(__file__)
SKEL_DIR = os.path.join(BASE_PATH, skeleton)
VERSION_FILE = os.path.join(package, 'version.py')


def read(file):
    """

    :param file:
    :return:
    """
    with open(os.path.join(BASE_PATH, file)) as f:
        return f.read()


def grep(file, name):
    """

    :param file:
    :param name:
    :return:
    """
    pattern = r"{attr}\W*=\W*'([^']+)'".format(attr=name)
    value, = re.findall(pattern, read(file))
    return value


def readme(file):
    """

    :param file:
    :return:
    """
    try:
        return read(file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)


class PyTest(test):
    def finalize_options(self):
        """

        """
        test.finalize_options(self)

    def run_tests(self):
        """

        """
        import pytest
        sys.exit(pytest.main(['tests']))


def package_files(directory):
    """

    :param directory:
    :return:
    """
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))

    return paths


try:
    os.symlink(SKEL_DIR, os.path.join(package, skeleton))

    setup(
        name='Flaskel',
        license='MIT',
        version=grep(VERSION_FILE, '__version__'),
        url='https://github.com/cs91chris/flaskel',
        author=grep(VERSION_FILE, '__author_name__'),
        author_email=grep(VERSION_FILE, '__author_email__'),
        description='Skeleton for flask applications',
        long_description=readme('README.rst'),
        platforms='any',
        python_requires='>3.6',
        zip_safe=False,
        packages=find_packages(),
        include_package_data=True,
        package_data={
            package: package_files(skeleton)
        },
        entry_points={
            'console_scripts': [
                'flaskel = flaskel.cli:cli',
            ],
        },
        install_requires=[
            "Flask==1.1.*",
            "Flask-APScheduler==1.11.*",
            "Flask-Caching==1.9.*",
            "Flask-CloudflareRemote==1.1.*",
            "Flask-Cors==3.0.*",
            "Flask-ErrorsHandler==3.0.*",
            "Flask-HTTPAuth==4.2.*",
            "Flask-JWT-Extended==3.25.*",
            "Flask-Limiter==1.4.*",
            "Flask-Logify==2.2.3",
            "Flask-Mail==0.9.*",
            "Flask-ResponseBuilder==2.0.*",
            "Flask-SQLAlchemy==2.4.*",
            "Flask-TemplateSupport==2.0.*",
            "aiohttp==3.7.*",
            "argon2-cffi==20.1.*",
            "coverage==5.3.*",
            "nest-asyncio==1.5.*",
            "psutil==5.8.*",
            "pytest==6.2.*",
            "pytest-cov==2.10.*",
            "python-dateutil==2.8.*",
            "python-decouple==3.4.*",
            "PyYAML==5.4.*",
            "requests==2.25.*",
            "simplejson-3.*",
            "sqlalchemy-schemadisplay==1.3.*",
            "user-agents==2.2.*",
            "webargs==7.0.*",
        ],
        extras_requires={},
        cmdclass={'test': PyTest},
        test_suite='tests',
        classifiers=[
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'Topic :: Software Development :: Libraries :: Python Modules'
        ]
    )
finally:
    os.unlink(os.path.join(package, skeleton))
