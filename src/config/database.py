import os
from sqlmodel import create_engine, SQLModel
from fastapi import Depends
from sqlmodel import  Session
from typing import Annotated

# DATABASE_URL = "mysql+mysqlconnector://shayon:Test1234@localhost/football_stats"  # Update with your MySQL credentials
#
# engine = create_engine(DATABASE_URL, echo=True)

mysql_url = os.getenv("MYSQL_URI", None)

engine = create_engine(mysql_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
