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
            "Flask",
            "Flask-Cors",
            "Flask-ErrorsHandler",
            "Flask-ResponseBuilder",
            "Flask-TemplateSupport",
            "Flask-CloudflareRemote",
            "Flask-Logify",
            "Flask-SqlAlchemy",
            "Flask-JWT-Extended",
            "Flask-Limiter",
            "Flask-Caching",
            "Flask-HTTPAuth",
            "sqlalchemy_schemadisplay",
            "PyYAML",
            "requests",
            "user-agents",
            "argon2-cffi",
            "jsonschema",
            "webargs",
            "python-decouple",
            "psutil",
            "pytest==6.2.*",
            "pytest-cov==2.10.*",
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
