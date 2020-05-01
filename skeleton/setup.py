# generated via cli
import os
import re
import sys

from setuptools.command.test import test
from setuptools import setup, find_packages

BASE_PATH = os.path.dirname(__file__)
VERSION_FILE = os.path.join('{skeleton}', 'version.py')


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


setup(
    name='',
    url='',
    license='MIT',
    version=grep(VERSION_FILE, '__version__'),
    author=grep(VERSION_FILE, '__author_name__'),
    author_email=grep(VERSION_FILE, '__author_email__'),
    description='Skeleton for flask applications',
    long_description=readme('README.rst'),
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'flaskel-app = cli:cli',
        ],
    },
    install_requires=[
        "flaskel"
    ],
    tests_require=[
        'pytest',
        'pytest-cov'
    ],
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
