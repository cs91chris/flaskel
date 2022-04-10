#!/bin/bash

pip install -r requirements/requirements-build.txt

python setup.py sdist
python setup.py bdist_wheel
