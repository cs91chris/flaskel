# generated via cli
import os
import re
import sys

from setuptools import find_packages as base_find_packages
from setuptools import setup
from setuptools.command.test import test

LICENSE = "MIT"
URL = None
PLATFORMS = "any"
PYTHON_VERSION = ">3.6"
DESCRIPTION = None
PACKAGE_DATA = True

PKG_NAME = "{skeleton}"
PKG_TEST = "tests"
PKG_SCRIPTS = f"{PKG_NAME}.scripts"

EXCLUDE_FILES = []  # type: ignore

REQUIRES = ["flaskel"]

ENTRY_POINTS = dict(
    console_scripts=[
        f"run-{PKG_NAME}={PKG_SCRIPTS}.cli:cli",
    ],
)

BASE_PATH = os.path.dirname(__file__)
VERSION_FILE = os.path.join(PKG_NAME, "skel/version.py")

try:
    # must be after setuptools
    # noinspection PyPackageRequirements
    from Cython.Build import cythonize as base_cythonize

    # noinspection PyPackageRequirements
    import Cython.Compiler.Options as cython_options

    cython_options.docstrings = False
except ImportError:
    cython_options = None
    base_cythonize = None

if "--cythonize" not in sys.argv:
    base_cythonize = None
else:
    sys.argv.remove("--cythonize")


def ext_paths(root_dir, exclude=()):
    paths = []
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_ext = filename.split(".")[-1]
            if file_path in exclude or file_ext not in ("py", "pyx"):
                continue

            paths.append(file_path)
    return paths


def read(file):
    with open(os.path.join(BASE_PATH, file)) as f:
        return f.read()


def grep(file, name):
    (value,) = re.findall(fr"{name}\W*=\W*'([^']+)'", read(file))
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


def cythonize(paths):
    if base_cythonize is not None:
        return base_cythonize(paths, language_level=3)


def find_packages():
    if base_cythonize is not None:
        return [PKG_SCRIPTS]
    return base_find_packages(exclude=(PKG_TEST, f"{PKG_TEST}.*"))


setup(
    name=PKG_NAME,
    url=URL,
    license=LICENSE,
    description=DESCRIPTION,
    platforms=PLATFORMS,
    python_requires=PYTHON_VERSION,
    long_description=readme("README.rst"),
    version=grep(VERSION_FILE, "__version__"),
    author=grep(VERSION_FILE, "__author_name__"),
    author_email=grep(VERSION_FILE, "__author_email__"),
    zip_safe=False,
    include_package_data=PACKAGE_DATA,
    packages=find_packages(),
    ext_modules=cythonize(ext_paths(PKG_NAME, EXCLUDE_FILES)),
    entry_points=ENTRY_POINTS,
    test_suite=PKG_TEST,
    install_requires=REQUIRES,
    cmdclass=dict(test=PyTest),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "License :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
)
