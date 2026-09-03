import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.deps import get_db
from app.config import get_settings
from app.database import Base
from app.main import app
from services.llm_service import LLMNotConfiguredError


@pytest.fixture(autouse=True)
def no_live_llm_calls(monkeypatch):
    """Tests must never depend on network access or a real API key — force
    every analysis in the test suite through the deterministic fallback
    path. The live LLM path is covered separately with a scripted fake
    client in test_agent.py.
    """

    def _raise_not_configured():
        raise LLMNotConfiguredError("disabled during tests")

    monkeypatch.setattr("ai.agent.get_llm_client", _raise_not_configured)


def _test_database_url() -> str:
    settings = get_settings()
    base, _, _ = settings.database_url.rpartition("/")
    return f"{base}/spendly_test"


@pytest.fixture()
def db_session():
    engine = create_engine(_test_database_url())
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
