import sys

import pytest


def main():
    pytest.main(
        [
            "-v",
            "-rf",
            "--strict-markers",
            "-p",
            "flaskel.tester.plugins.fixtures",
            "-p",
            "flaskel.tester.plugins.startup",
            *sys.argv[1:],
        ]
    )


if __name__ == "__main__":
    main()
