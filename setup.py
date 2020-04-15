"""
Flaskel
-------------
"""
import sys

import pytest
from setuptools.command.test import test
from setuptools import setup, find_packages

from flaskel import __author_info__, __version__

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
    name='Flaskel',
    version=__version__,
    url='https://github.com/cs91chris/flaskel',
    license='MIT',
    author=__author_info__['name'],
    author_email=__author_info__['email'],
    description='Skeleton for flask applications',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        "PyYAML",
        "Flask==1.1.*",
        "Flask-Cors==3.0.*",
        "Flask-ErrorsHandler==2.*",
        "Flask-ResponseBuilder==2.*",
        "Flask-TemplateSupport==1.*",
        "Flask-CloudflareRemote==1.*",
        "Flask-Logify==1.*",
        "argon2-cffi==19.2.*",
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
