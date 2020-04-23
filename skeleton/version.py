__version_info__ = (0, 0, 0)
__version__ = '.'.join(map(str, __version_info__))

__cli_name__ = 'appctl'

__author_info__ = {
    'name': '',
    'email': ''
}

__author__ = "{} <{}>".format(
    __author_info__['name'],
    __author_info__['email']
)

__all__ = [
    '__version_info__',
    '__version__',
    '__author__',
    '__author_info__',
    '__cli_name__',
]
