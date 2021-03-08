"""
Flaskel
-------
"""
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

PKG_NAME = 'flaskel'
PKG_TEST = 'tests'
SKELETON = 'skeleton'
BASE_PATH = os.path.dirname(__file__)
SKEL_DIR = os.path.join(BASE_PATH, SKELETON)
VERSION_FILE = os.path.join(BASE_PATH, PKG_NAME, 'version.py')
EXCLUDE_FILES = [
    f"{PKG_NAME}/cli.py",
    f"{PKG_NAME}/tester/cli.py"
]

REQUIRES = [
    "Flask==1.1.*",
    "Flask-APScheduler==1.11.*",
    "Flask-Caching==1.9.*",
    "Flask-CloudflareRemote==1.1.*",
    "Flask-Cors==3.0.*",
    "Flask-ErrorsHandler==4.0.*",
    "Flask-HTTPAuth==4.2.*",
    "Flask-JWT-Extended==3.25.*",
    "Flask-Limiter==1.4.*",
    "Flask-Logify==2.2.3",
    "Flask-Mail==0.9.*",
    "Flask-ResponseBuilder==2.0.*",
    "Flask-SQLAlchemy==2.4.*",
    "Flask-TemplateSupport==2.0.*",
    "aiohttp==3.7.*",
    "argon2-cffi==20.1.*",
    "coverage==5.3.*",
    "nest-asyncio==1.5.*",
    "psutil==5.8.*",
    "pytest==6.2.*",
    "pytest-cov==2.10.*",
    "python-dateutil==2.8.*",
    "python-decouple==3.4.*",
    "PyYAML==5.4.*",
    "requests==2.25.*",
    "simplejson==3.*",
    "sqlalchemy-schemadisplay==1.3.*",
    "user-agents==2.2.*",
    "webargs==7.0.*",
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


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))

    return paths


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(['tests']))


try:
    os.symlink(SKEL_DIR, os.path.join(BASE_PATH, PKG_NAME, SKELETON))
    setup(
        name='Flaskel',
        license='MIT',
        version=grep(VERSION_FILE, '__version__'),
        url='https://github.com/cs91chris/flaskel',
        author=grep(VERSION_FILE, '__author_name__'),
        author_email=grep(VERSION_FILE, '__author_email__'),
        description='Skeleton for flask applications',
        long_description=readme('README.rst'),
        platforms='any',
        python_requires='>3.6',
        zip_safe=False,
        test_suite=PKG_TEST,
        include_package_data=True,
        packages=find_packages(include=(PKG_NAME, f"{PKG_NAME}.*")),
        package_data={
            PKG_NAME: package_files(SKEL_DIR)
        },
        ext_modules=None if not cythonize else cythonize(
            get_ext_paths(PKG_NAME, EXCLUDE_FILES),
            compiler_directives={'language_level': 3}
        ),
        entry_points={
            'console_scripts': [
                f"{PKG_NAME}={PKG_NAME}.cli:cli",
            ],
        },
        cmdclass={
            'test':     PyTest,
            'build_py': BuildWheel,
        },
        install_requires=REQUIRES,
        classifiers=[]
    )
finally:
    os.unlink(os.path.join(BASE_PATH, PKG_NAME, SKELETON))
