import os
import shutil
import sys
from pathlib import Path


def replace_in_file(file, *args):
    _f = Path(file)
    text = _f.read_text(encoding="utf-8")
    for sd in args:
        text = text.replace(*sd)
    _f.write_text(text, encoding="utf-8")


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
    placeholder = "{skeleton}"
    init_file = Path(os.path.join(name, "__init__.py"))
    init_file.write_text("from .version import *\n", encoding="utf-8")
    service_dir = os.path.join("devops", "services", name)
    shutil.move(os.path.join("devops", "services", "skel"), service_dir)

    for args in (
        ("setup.py", (placeholder, name)),
        ("Makefile", (placeholder, name)),
        ("pytest.ini", (placeholder, name)),
        (".coveragerc", (placeholder, name)),
        (".bumpversion.cfg", (placeholder, name)),
        (os.path.join("devops", "Dockerfile"), (placeholder, name)),
        (os.path.join("devops", "docker-compose.yaml"), (placeholder, name)),
        (os.path.join(service_dir, "settings.ini"), (placeholder, name)),
        (os.path.join(service_dir, "env"), (placeholder, name)),
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
