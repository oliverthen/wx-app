from fastapi import Depends, HTTPException, FastAPI, Form, Request
from decouple import config
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse 
from sqlmodel import Session, select

from .models import User, get_session, create_db_and_tables

import requests

app = FastAPI()

@app.on_event("startup")
def on_startup():
	create_db_and_tables()
	

templates = Jinja2Templates(directory="templates")

key_api = config('API_KEY')

def convert_celsius_to_fahrenheight(temp_celsius: float) -> float:
	return (temp_celsius * 9/5) + 32

def convert_kelvin_to_celsius(temp_kelvin: float) -> float:
	return temp_kelvin - 273.15



@app.get("/", response_class=HTMLResponse)
async def get_coordinates(request: Request):
	return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_coordinates", response_class=HTMLResponse)
async def process_coordinates(
	request: Request,
	latitude: float = Form(...),
	longitude: float = Form(...)
):
	
	url = f'https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&appid={key_api}'

	response = requests.get(url)
	data = response.json()
	
	temp_c = convert_kelvin_to_celsius(data['current']['temp'])

	temp_f = convert_celsius_to_fahrenheight(temp_c)


	return templates.TemplateResponse("weather.html", {"request": request, "temp_c": round(temp_c), "temp_f": round(temp_f)})

@app.post("/register")
def register_user(*, session: Session = Depends(get_session), user: User):
	query = select(User).where(User.handle == user.handle)
	existing_user = session.exec(query).first()
	if existing_user is not None:
		raise HTTPException(status_code=400, detail="User already exists")
	db_user = User.from_orm(user)
	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

