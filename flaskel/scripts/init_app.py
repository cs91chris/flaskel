import os
import shutil
import sys
from pathlib import Path


def replace_in_file(file, *args):
    _f = Path(file)
    text = _f.read_text()
    for sd in args:
        text = text.replace(*sd)
    _f.write_text(text)


def copy_skeleton(name):
    from flaskel import scripts as flaskel_scripts  # pylint: disable=C0415

    try:
        source = os.path.join(flaskel_scripts.__path__[0], "skeleton")
        shutil.copytree(source, ".", dirs_exist_ok=True)
        shutil.move("skel", name)
    except OSError as e:
        print(f"Unable to create new app. Error: {e}", file=sys.stderr)
        sys.exit(1)


def init_app(name):
    copy_skeleton(name)

    init_file = Path(os.path.join(name, "__init__.py"))
    init_file.write_text("from .version import *\n")
    service_dir = os.path.join("devops", "services", name)
    shutil.move(os.path.join("devops", "services", "skel"), service_dir)

    for args in (
        (
            "setup.py",
            ("{skeleton}", name),
        ),
        (
            "Makefile",
            ("{skeleton}", name),
        ),
        (
            "pytest.ini",
            ("{skeleton}", name),
        ),
        (
            ".coveragerc",
            ("{skeleton}", name),
        ),
        (
            ".bumpversion.cfg",
            ("{skeleton}", name),
        ),
        (
            os.path.join("devops", "Dockerfile"),
            ("{skeleton}", name),
        ),
        (
            os.path.join("devops", "docker-compose.yaml"),
            ("{skeleton}", name),
        ),
        (
            os.path.join(service_dir, "settings.ini"),
            ("{skeleton}", name),
        ),
        (
            os.path.join(service_dir, "env"),
            ("{skeleton}", name),
        ),
        (
            os.path.join(name, "scripts", "cli.py"),
            ("from ext", f"from {name}.ext"),
            ("from views", f"from {name}.views"),
        ),
        (
            os.path.join(name, "scripts", "gunicorn.py"),
            ("from . import config", f"from {name}.scripts import config"),
        ),
        (
            os.path.join("tests", "__init__.py"),
            ("from scripts.cli", f"from {name}.scripts.cli"),
        ),
    ):
        replace_in_file(*args)
