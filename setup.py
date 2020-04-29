"""
Flaskel
-------------
"""
import os
import sys

import pytest
from setuptools.command.test import test
from setuptools import setup, find_packages

from flaskel import __author_info__, __version__

package = 'flaskel'
skeleton = 'skeleton'
base_dir = os.path.abspath(os.path.dirname(__file__))
skeleton_dir = os.path.join(base_dir, skeleton)


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
    os.symlink(skeleton_dir, os.path.join(package, skeleton))

    setup(
        name='Flaskel',
        version=__version__,
        url='https://github.com/cs91chris/flaskel',
        license='MIT',
        author=__author_info__['name'],
        author_email=__author_info__['email'],
        description='Skeleton for flask applications',
        long_description=long_description,
        platforms='any',
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
            "PyYAML==5.*",
            "Flask==1.1.*",
            "Flask-Cors==3.0.*",
            "Flask-ErrorsHandler==3.*",
            "Flask-ResponseBuilder==2.*",
            "Flask-TemplateSupport==1.*",
            "Flask-CloudflareRemote==1.*",
            "Flask-Logify==1.*",
            "argon2-cffi==19.*",
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
finally:
    os.unlink(os.path.join(package, skeleton))
