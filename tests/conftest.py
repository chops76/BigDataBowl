import pytest

from databowl.download import RAW_DIR, has_data


def pytest_collection_modifyitems(config, items):
    """Skip tests marked @pytest.mark.data when the real data isn't downloaded."""
    if has_data(RAW_DIR):
        return
    skip = pytest.mark.skip(reason="real data not downloaded (run `make data`)")
    for item in items:
        if "data" in item.keywords:
            item.add_marker(skip)
