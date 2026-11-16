import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Settings
from app.main import app
from app.deps import get_settings


@pytest.fixture()
def client(tmp_path):
    """TestClient с временной SQLite-базой; файл удаляется после теста."""
    db_path = str(tmp_path / "test.db")

    def test_settings() -> Settings:
        return Settings(database_path=db_path)

    app.dependency_overrides[get_settings] = test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
