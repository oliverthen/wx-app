from typing import Optional

from sqlmodel import Field, SQLModel, Session, create_engine

class User(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	first_name: str
	last_name: str
	email: str
	zip_code: int
	password: str

engine = create_engine("sqlite:///database.db")