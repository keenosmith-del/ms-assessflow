import os

os.environ["ASSESSFLOW_ENV_FILE"] = "/dev/null"
os.environ["ASSESSFLOW_MODE"] = "demo"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite://")
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.db.session import Base, get_db
from app.db.seed import seed
from app.main import app, windows


@pytest.fixture
def client():
    url = os.environ["DATABASE_URL"]
    kwargs = (
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        if url == "sqlite://"
        else {}
    )
    engine = create_engine(url, **kwargs)
    # TEST_DATABASE_URL must point to a disposable database, never production.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory.begin() as db:
        seed(db)

    def session():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = session
    windows.clear()
    with TestClient(app) as value:
        value.factory = factory
        yield value
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def employee():
    return {"X-Demo-User": "employee"}
