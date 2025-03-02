import pytest
from pathlib import Path

def pytest_addoption(parser):
    parser.addoption("--root_path", action="store", default=".", help="Root directory path")

@pytest.fixture(scope="session")
def root_path(pytestconfig):
    return Path(pytestconfig.getoption("--root_path")).resolve()
