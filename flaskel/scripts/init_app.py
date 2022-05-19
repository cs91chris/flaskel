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


def copy_skeleton(name: str):
    from flaskel import scripts as flaskel_scripts  # pylint: disable=C0415

    try:
        source = os.path.join(flaskel_scripts.__path__[0], "skeleton")
        shutil.copytree(source, ".", dirs_exist_ok=True)
        shutil.move("skel", name)
    except OSError as e:
        print(f"Unable to create new app. Error: {e}", file=sys.stderr)
        sys.exit(1)


def fix_files_references(name: str, placeholder: str):
    for args in (
        (
            os.path.join(name, "scripts", "cli.py"),
            ("from ext", f"from {name}.ext"),
            ("from views", f"from {name}.views"),
        ),
        (
            os.path.join("tests", "conftest.py"),
            ("from scripts.cli", f"from {name}.scripts.cli"),
        ),
        (
            os.path.join("tests", "conftest.py"),
            (placeholder, name),
        ),
    ):
        replace_in_file(*args)


def init_app(name: str, placeholder: str = "{skeleton}"):
    copy_skeleton(name)
    init_file = Path(os.path.join(name, "__init__.py"))
    init_file.write_text("from .version import *\n", encoding="utf-8")
    fix_files_references(name, placeholder)
