from app.db.base import Base
from app.db import models  # noqa: F401
from app.db.session import engine


def ensure_runtime_schema() -> None:
    Base.metadata.create_all(bind=engine)
