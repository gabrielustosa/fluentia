from sqlalchemy import create_engine
from sqlmodel import Session

from fluentia.settings import Settings

engine = create_engine(Settings().database_url('fluentia'))


def get_session():
    with Session(engine) as session:
        yield session
