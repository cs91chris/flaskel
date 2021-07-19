import pytest

MARKERS = {
    "smoke": {"description": "smoke tests", "marker": pytest.mark.smoke},
    "email": {"description": "email tests", "marker": pytest.mark.email},
    "integ": {"description": "integration tests", "marker": pytest.mark.integ},
    "infra": {"description": "infrastructure tests", "marker": pytest.mark.infra},
}


def pytest_configure(config):
    """

    :param config:
    """
    for k, v in MARKERS.items():
        config.addinivalue_line("markers", "{}: {}".format(k, v["description"]))
