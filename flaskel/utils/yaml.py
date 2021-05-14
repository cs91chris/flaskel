# based on:
# https://github.com/nameko/nameko/blob/a719cb1487f643769e2d13daf255c20551490f43/nameko/cli/main.py#L102-L111

import os
import re
import sys
from functools import partial

import yaml

from .datastruct import ObjectDict

ENV_VAR_MATCHER = re.compile(
    r"""
        \${        # match characters `${` literally
        ([^}:\s]+) # 1st group: matches any character except `}` or `:`
        :?         # matches the literal `:` character zero or one times
        ([^}]+)?   # 2nd group: matches any character except `}`
        }          # match character `}` literally
    """, re.VERBOSE
)

IMPLICIT_ENV_VAR_MATCHER = re.compile(
    r"""
        .*      # matches any number of any characters
        \${.*}  # matches any number of any characters
                # between `${` and `}` literally
        .*      # matches any number of any characters
    """, re.VERBOSE
)


def loads(data, loader=None):
    return ObjectDict.normalize(yaml.load(data, Loader=loader or yaml.Loader))


def load_yaml_file(filename, **kwargs):
    with open(filename) as f:
        return loads(f, **kwargs)


def load_optional_yaml_file(filename, default=None, **kwargs):
    try:
        return load_yaml_file(filename, **kwargs)
    except OSError as exc:
        print(f"WARN: {exc}", file=sys.stderr)
        return ObjectDict() if default is None else default


def _replace_env_var(match):
    env_var, default = match.groups()
    value = os.environ.get(env_var, None)
    if value is None:
        if default is None:
            # regex module return None instead of '' if engine didn't entered default capture group
            default = ''

        value = default
        while IMPLICIT_ENV_VAR_MATCHER.match(value):
            value = ENV_VAR_MATCHER.sub(_replace_env_var, value)
    return value


def env_var_constructor(loader, node, raw=False):
    raw_value = loader.construct_scalar(node)
    value = ENV_VAR_MATCHER.sub(_replace_env_var, raw_value)
    return value if raw else yaml.safe_load(value)


def include_constructor(loader, node):
    return load_yaml_file(node.value, loader=loader.__class__)


def optional_include_constructor(loader, node):
    return load_optional_yaml_file(node.value, loader=loader.__class__)


yaml.add_constructor('!include', include_constructor)
yaml.add_constructor('!opt_include', optional_include_constructor)
yaml.add_constructor('!env_var', env_var_constructor)
yaml.add_constructor('!raw_env_var', partial(env_var_constructor, raw=True))
yaml.add_implicit_resolver('!env_var', IMPLICIT_ENV_VAR_MATCHER)
