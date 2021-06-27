"""
Flaskel
-------
"""
import os
import re
import sys

from setuptools import find_packages as base_find_packages, setup
from setuptools.command.test import test

LICENSE = 'MIT'
PLATFORMS = 'any'
PYTHON_VERSION = '>3.6'
URL = 'https://github.com/cs91chris/flaskel'
DESCRIPTION = 'Skeleton for flask applications'

PKG_NAME = 'flaskel'
PKG_TEST = 'tests'
PKG_SCRIPTS = f'{PKG_NAME}.scripts'

ENTRY_POINTS = dict(
    console_scripts=[
        f"{PKG_NAME}={PKG_SCRIPTS}.cli:cli",
    ],
)

REQUIRES = [
    "Flask==2.0.*",
    "Flask-APScheduler==1.12.*",
    "Flask-Caching==1.10.*",
    "Flask-CloudflareRemote==1.1.*",
    "Flask-Cors>=3.0.0",
    "Flask-ErrorsHandler==4.0.*",
    "Flask-HTTPAuth>=4.4.*",
    "Flask-JWT-Extended>=4.2.1",
    "Flask-Limiter==1.4.*",
    "Flask-Logify==2.4.*",
    "Flask-Mail==0.9.*",
    "Flask-ResponseBuilder==2.0.*",
    "Flask-SQLAlchemy==2.5.*",
    "Flask-TemplateSupport==2.0.*",
    "aiohttp==3.7.*",
    "argon2-cffi==20.1.*",
    "coverage==5.5.*",
    "nest-asyncio==1.5.*",
    "psutil==5.8.*",
    "pytest==6.2.*",
    "pytest-cov==2.11.*",
    "python-dateutil==2.8.*",
    "python-decouple==3.4.*",
    "PyYAML==5.4.*",
    "requests==2.25.*",
    "jsonschema==3.2.*",
    "simplejson==3.*",
    "sqlalchemy-schemadisplay==1.3.*",
    "user-agents==2.2.*",
    "webargs==8.0.*",
    "redis==3.5.*",
    "hiredis==2.0.*",
]

BASE_PATH = os.path.dirname(__file__)
SKEL_DIR = os.path.join(*PKG_SCRIPTS.split('.'), 'skeleton')
VERSION_FILE = os.path.join(BASE_PATH, PKG_NAME, 'version.py')

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
            file_ext = filename.split('.')[-1]
            if file_path in exclude or file_ext not in ('py', 'pyx'):
                continue

            paths.append(file_path)
    return paths


def read(file):
    with open(os.path.join(BASE_PATH, file)) as f:
        return f.read()


def grep(file, name):
    value, = re.findall(fr"{name}\W*=\W*'([^']+)'", read(file))
    return value


def readme(file):
    try:
        return read(file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)


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
        import pytest
        sys.exit(pytest.main([PKG_TEST]))


def cythonize(paths):
    if base_cythonize is not None:
        return base_cythonize(paths, language_level=3)


def find_packages():
    if base_cythonize is not None:
        return [PKG_SCRIPTS]
    return base_find_packages()


setup(
    name='Flaskel',
    url=URL,
    license=LICENSE,
    description=DESCRIPTION,
    platforms=PLATFORMS,
    python_requires=PYTHON_VERSION,
    long_description=readme('README.md'),
    long_description_content_type='text/markdown',
    version=grep(VERSION_FILE, '__version__'),
    author=grep(VERSION_FILE, '__author_name__'),
    author_email=grep(VERSION_FILE, '__author_email__'),
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    ext_modules=cythonize(ext_paths(PKG_NAME, skeleton_files())),
    test_suite=PKG_TEST,
    entry_points=ENTRY_POINTS,
    cmdclass=dict(test=PyTest),
    install_requires=REQUIRES,
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
    ]
)
