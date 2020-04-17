import sys

import pytest
from setuptools.command.test import test
from setuptools import setup, find_packages

__version__ = ''
__author_info__ = {
    'name': '',
    'email': ''
}

with open("README.md") as fh:
    long_description = fh.read()


class PyTest(test):
    def finalize_options(self):
        """

        """
        test.finalize_options(self)

    def run_tests(self):
        """

        """
        sys.exit(pytest.main(['tests']))


setup(
    name='',
    version=__version__,
    url='',
    license='MIT',
    author=__author_info__['name'],
    author_email=__author_info__['email'],
    description='Skeleton for flask applications',
    long_description=long_description,
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyYAML",
        "flaskel",
        "gunicorn",
        "meinheld"
    ],
    tests_require=[
        'pytest==5.4.*',
        'pytest-cov==2.8.*'
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
