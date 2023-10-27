from fastapi import Depends, HTTPException, FastAPI, Form, Request
from decouple import config
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from models import User, get_session, create_db_and_tables

import requests

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


templates = Jinja2Templates(directory="templates")

key_api = config("API_KEY")


def convert_celsius_to_fahrenheight(temp_celsius: float) -> float:
    return (temp_celsius * 9 / 5) + 32


def convert_kelvin_to_celsius(temp_kelvin: float) -> float:
    return temp_kelvin - 273.15

def _process_zip(zipcode):
    """Called by functions get_lat_zip or get_lon_zip to return JSON data of location specificied by zipcode"""
    zip_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={zipcode},US&appid={key_api}"

    zip_response = requests.get(zip_url)
    return zip_response.json()

def _process_city_state(city, state):
    """Called by functions get_lat_city or get_lon_city to return JSON data of location specificied by city and name"""
    city_state_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},{state},US&appid={key_api}"

    city_state_response = requests.get(city_state_url)

    return city_state_response.json()

def get_lat_lon_zip(zipcode):
    """Receives JSON data of location specified by zip code entered and returns tuple with latitude and longitude of location"""
    zip_data = _process_zip(zipcode)
    return (zip_data["lat"], zip_data["lon"])


def get_lat_lon_city(city, state):
    """Receives JSON data of location specified by city and state entered and returns tuple with latitude and longitude of location"""
    city_data = _process_city_state(city, state)
    return (city_data[0]["lat"], city_data[0]["lon"])

def get_location_name(latitude, longitude):
    """Based upon coordinates, returns name of location"""
    geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&appid={key_api}"

    geo_response = requests.get(geo_url)
    response = geo_response.json()
    print(response)
    
    return (response[0]["name"], response[0]["state"])

@app.get("/", response_class=HTMLResponse)
async def get_coordinates(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_zip_or_city", response_class=HTMLResponse)
async def return_data(
    request: Request, zipcode: str = Form(None), city: str = Form(None), state: str = Form(None)
):
    """Route that handles zipcode or city and state to return weather data"""
    
    if zipcode is not None:
        (latitude, longitude) = get_lat_lon_zip(zipcode)        
    else:
        (latitude, longitude) = get_lat_lon_city(city, state)
    
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&appid={key_api}"

    response = requests.get(url)
    data = response.json()

    (loc_name, loc_state) = get_location_name(latitude, longitude)
    location_name = f"{loc_name}, {loc_state}"

    temp_c = convert_kelvin_to_celsius(data["current"]["temp"])
    temp_f = convert_celsius_to_fahrenheight(temp_c)

    return templates.TemplateResponse(
        "weather.html",
        {"request": request, "location_name": location_name, "temp_c": round(temp_c), "temp_f": round(temp_f)},
    )


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
