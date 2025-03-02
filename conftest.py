import pytest
from pathlib import Path

def pytest_addoption(parser):
    """pytest에 --root_path 옵션 추가"""
    parser.addoption("--root_path", action="store", default=".", help="Root directory path")

@pytest.fixture(scope="session")
def root_path(pytestconfig):
    """pytest에서 --root_path 옵션을 가져와서 반환"""
    return Path(pytestconfig.getoption("--root_path")).resolve()
