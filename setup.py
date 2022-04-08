"""
Flaskel
-------
"""
import os
import re
import sys

from pkg_resources import parse_requirements
from setuptools import find_packages as base_find_packages, setup
from setuptools.command.test import test

LICENSE = "MIT"
PLATFORMS = "any"
PYTHON_VERSION = ">3.6"
URL = "https://github.com/cs91chris/flaskel"
DESCRIPTION = "Skeleton for flask applications"

PKG_NAME = "flaskel"
PKG_TEST = "tests"
PKG_SCRIPTS = f"{PKG_NAME}.scripts"

BASE_PATH = os.path.dirname(__file__)
SKEL_DIR = os.path.join(*PKG_SCRIPTS.split("."), "skeleton")
VERSION_FILE = os.path.join(BASE_PATH, PKG_NAME, "version.py")
REQUIRES = [
    "Flask",
    "Flask-Caching",
    "Flask-CloudflareRemote",
    "Flask-Cors",
    "Flask-ErrorsHandler",
    "Flask-HTTPAuth",
    "Flask-JWT-Extended",
    "Flask-Limiter",
    "Flask-Logify",
    "Flask-ResponseBuilder",
    "Flask-SQLAlchemy",
    "Flask-TemplateSupport",
    "webargs",
    "aiohttp",
    "nest-asyncio",
    "vbcore[all]",
]
REQUIRES_EXT = REQUIRES + [
    "pyfcm",
    "stripe",
    "redis",
    "rejson",
    "hiredis",
    "Flask-Mail",
    "Flask-APScheduler",
    "flask_pymongo",
]
REQUIRES_TEST = REQUIRES_EXT + [
    "coverage",
    "pytest",
    "pytest-cov",
]

ENTRY_POINTS = dict(
    console_scripts=[
        f"{PKG_NAME}={PKG_SCRIPTS}.cli:cli",
    ]
)

try:
    # must be after setuptools
    # noinspection PyPackageRequirements
    # noinspection PyPackageRequirements,PyPep8Naming
    import Cython.Compiler.Options as cython_options
    from Cython.Build import cythonize as base_cythonize

    cython_options.docstrings = False
except ImportError:
    cython_options = None
    base_cythonize = None

if "--cythonize" not in sys.argv:
    base_cythonize = None  # pylint: disable=C0103
else:
    sys.argv.remove("--cythonize")


def ext_paths(root_dir, exclude=()):
    paths = []
    for root, _, files in os.walk(root_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_ext = filename.split(".")[-1]
            if file_path in exclude or file_ext not in ("py", "pyx"):
                continue

            paths.append(file_path)
    return paths


def read(file):
    with open(os.path.join(BASE_PATH, file), encoding="utf-8") as f:
        return f.read()


def grep(file, name):
    values = re.findall(rf"{name}\W*=\W*\"([^\"]+)", read(file))
    return values[0] if values else None


def readme(file):
    try:
        return read(file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
    return None


def read_requirements(filename):
    return [str(req) for req in parse_requirements(read(filename))]


def skeleton_files():
    paths = []
    for path, _, filenames in os.walk(SKEL_DIR):
        for f in filenames:
            paths.append(os.path.join(path, f))
    return paths


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        import pytest  # pylint: disable=C0415

        sys.exit(pytest.main([PKG_TEST]))


def cythonize(paths):
    if base_cythonize is not None:
        # noinspection PyCallingNonCallable
        return base_cythonize(paths, language_level=3)
    return None


def find_packages():
    if base_cythonize is not None:
        return [PKG_SCRIPTS]
    return base_find_packages(exclude=(PKG_TEST, f"{PKG_TEST}.*"))


setup(
    name="Flaskel",
    url=URL,
    license=LICENSE,
    description=DESCRIPTION,
    platforms=PLATFORMS,
    python_requires=PYTHON_VERSION,
    long_description=readme("README.md"),
    long_description_content_type="text/markdown",
    version=grep(VERSION_FILE, "__version__"),
    author=grep(VERSION_FILE, "__author_name__"),
    author_email=grep(VERSION_FILE, "__author_email__"),
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    ext_modules=cythonize(ext_paths(PKG_NAME, skeleton_files())),
    test_suite=PKG_TEST,
    entry_points=ENTRY_POINTS,
    cmdclass=dict(test=PyTest),
    install_requires=REQUIRES,
    extras_require={
        "test": REQUIRES_TEST,
        "all": REQUIRES_EXT,
    },
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
)
