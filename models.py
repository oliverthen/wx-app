from typing import Optional

from sqlmodel import Field, SQLModel, Session, create_engine

class UserBase(SQLModel):
	first_name: str
	last_name: str
	username: str
	email: str
	zip_code: int
	password: str

class User(UserBase, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def get_session():
	with Session(engine) as session:
		yield session

def create_db_and_tables():
	SQLModel.metadata.create_all(engine)

# def create_user(db: Session, user: User):
# 	db.add(user)
# 	db.commit()
# 	db.refresh(user)