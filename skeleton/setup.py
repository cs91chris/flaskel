# generated via cli
import os
import re
import sys
import sysconfig

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.test import test

try:
    # must be after setuptools
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

PKG_NAME = '{skeleton}'
PKG_TEST = 'tests'

URL = ''
LICENSE = 'MIT'
DESCRIPTION = ''
CLASSIFIERS = []

BASE_PATH = os.path.dirname(__file__)
VERSION_FILE = os.path.join(PKG_NAME, 'version.py')

EXCLUDE_FILES = [
    f"{PKG_NAME}/cli.py",
]

REQUIRES = [
    "flaskel"
]


class BuildWheel(_build_py):
    def find_package_modules(self, package, package_dir):
        filtered_modules = []
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        for (pkg, mod, filepath) in super().find_package_modules(package, package_dir):
            if os.path.exists(filepath.replace('.py', ext_suffix)):
                continue
            filtered_modules.append((pkg, mod, filepath,))
        return filtered_modules


def get_ext_paths(root_dir, exclude_files):
    paths = []
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.py':
                continue
            file_path = os.path.join(root, filename)
            if file_path in exclude_files:
                continue

            paths.append(file_path)
    return paths


def read(file):
    with open(os.path.join(BASE_PATH, file)) as f:
        return f.read()


def grep(file, name):
    pattern = r"{attr}\W*=\W*'([^']+)'".format(attr=name)
    value, = re.findall(pattern, read(file))
    return value


def readme(file):
    try:
        return read(file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        import pytest
        sys.exit(pytest.main([PKG_TEST]))


setup(
    name=PKG_NAME,
    url=URL,
    license=LICENSE,
    description=DESCRIPTION,
    long_description=readme('README.rst'),
    version=grep(VERSION_FILE, '__version__'),
    author=grep(VERSION_FILE, '__author_name__'),
    author_email=grep(VERSION_FILE, '__author_email__'),
    platforms='any',
    python_requires='>3.6',
    zip_safe=False,
    install_requires=REQUIRES,
    test_suite=PKG_TEST,
    include_package_data=True,
    packages=find_packages(include=(PKG_NAME, f"{PKG_NAME}.*")),
    ext_modules=None if not cythonize else cythonize(
        get_ext_paths(PKG_NAME, EXCLUDE_FILES),
        compiler_directives={'language_level': 3}
    ),
    entry_points={
        'console_scripts': [
            f"run-{PKG_NAME} = {PKG_NAME}.cli:cli",
        ],
    },
    cmdclass={
        'test':     PyTest,
        'build_py': BuildWheel,
    },
    classifiers=CLASSIFIERS
)
