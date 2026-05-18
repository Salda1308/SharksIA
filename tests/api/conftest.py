import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models import Base

TEST_DB = "sqlite:///./storage/test.sqlite3"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    from api.main import app
    from api.database import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
