import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.deps import get_db
from app.config import get_settings
from app.database import Base
from app.main import app


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
