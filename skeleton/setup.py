# generated via cli
import sys

from setuptools.command.test import test
from setuptools import setup, find_packages

from .version import __version__, __author_info__


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


setup(
    name='',
    url='',
    license='MIT',
    version=__version__,
    author=__author_info__['name'],
    author_email=__author_info__['email'],
    description='Skeleton for flask applications',
    long_description=get_long_description(),
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
