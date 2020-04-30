"""
Flaskel
-------------
"""
import os
import sys

from setuptools.command.test import test
from setuptools import setup, find_packages

from flaskel import __author_info__, __version__

package = 'flaskel'
skeleton = 'skeleton'
base_dir = os.path.abspath(os.path.dirname(__file__))
skeleton_dir = os.path.join(base_dir, skeleton)


def get_long_description():
    """

    :return:
    """
    try:
        with open("README.md") as fh:
            return fh.read()
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
    os.symlink(skeleton_dir, os.path.join(package, skeleton))

    setup(
        name='Flaskel',
        version=__version__,
        url='https://github.com/cs91chris/flaskel',
        license='MIT',
        author=__author_info__['name'],
        author_email=__author_info__['email'],
        description='Skeleton for flask applications',
        long_description=get_long_description(),
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
            "PyYAML",
            "Flask",
            "Flask-Cors",
            "Flask-ErrorsHandler",
            "Flask-ResponseBuilder",
            "Flask-TemplateSupport",
            "Flask-CloudflareRemote",
            "Flask-Logify",
            "argon2-cffi",
            "requests",
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
finally:
    os.unlink(os.path.join(package, skeleton))
