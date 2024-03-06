from sqlalchemy import create_engine
from sqlmodel import Session

from fluentia.settings import Settings

engine = create_engine(Settings().DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session
