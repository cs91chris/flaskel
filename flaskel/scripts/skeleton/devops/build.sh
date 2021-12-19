#!/bin/bash

set -e

pip install -r requirements/requirements-build.txt

python setup.py bdist_wheel  # --cythonize
