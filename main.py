from fastapi import Depends, FastAPI, Form, Request
from decouple import config
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from sqlmodel import Session, select

from models import User, get_session, create_db_and_tables
from utils import get_hashed_password, verify_password

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

def _process_data(zipcode=None, city=None, state=None):
    """Returns tuple of variables to be displayed based on zipcode or city/state"""

    if zipcode is not None:
        (latitude, longitude) = get_lat_lon_zip(zipcode)        
    else:
        (latitude, longitude) = get_lat_lon_city(city, state)
    
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&appid={key_api}"

    response = requests.get(url)
    data = response.json()

    (loc_name, loc_state) = get_location_name(latitude, longitude)
    location_name = f"{loc_name}, {loc_state}"

    humidity = data["current"]["humidity"]
    pressure = data["current"]["pressure"]
    weather_description = data["current"]["weather"][0]["description"]

    temp_c = convert_kelvin_to_celsius(data["current"]["temp"])
    temp_f = convert_celsius_to_fahrenheight(temp_c)

    icon_code = data["current"]["weather"][0]["icon"]

    weather_icon = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

    return (location_name, humidity, pressure, weather_description, temp_c, temp_f, weather_icon)


@app.get("/", response_class=HTMLResponse)
async def get_location(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return templates.TemplateResponse("logout.html", {"request": request})


@app.post("/process_zip_or_city", response_class=HTMLResponse)
async def return_data(
    request: Request, zipcode: str = Form(None), city: str = Form(None), state: str = Form(None)
):
    """Route that handles zipcode or city and state to return weather data"""
    
    #Unpack tuple returned by helper _process_data which takes in either zip code or city/state info to generate targeted values to display on the front end
    (location_name, humidity, pressure, weather_description, temp_c, temp_f, weather_icon) = _process_data(zipcode, city, state)

    return templates.TemplateResponse(
        "weather.html",
        {"request": request, "location_name": location_name, "humidity": humidity, "pressure": pressure, "weather_description": weather_description, "temp_c": round(temp_c), "temp_f": round(temp_f), "weather_icon": weather_icon},
    )

@app.post("/register", response_model=User)
def process_regsitration(request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    zipcode: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
    ):


    user = User(
        first_name=first_name,
        last_name=last_name,
        zipcode=zipcode,
        email=email,
        password=get_hashed_password(password)
    )

    db_user = User.from_orm(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Render the user information template
    return templates.TemplateResponse("user_info.html", {"request": request, "db_user": db_user})

@app.post("/login")
def process_login(request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
    ):

    # Query the database to check if the email and password combination exists
    user = session.query(User).filter_by(email=email).first()

    if user and verify_password(password, user.password):
        # User is authenticated, redirect to the weather info for that user based on their zip code
        (location_name, humidity, pressure, weather_description, temp_c, temp_f, weather_icon) = _process_data(user.zipcode)

        return templates.TemplateResponse(
            "weather.html",
            {"request": request, "user": user, "location_name": location_name, "humidity": humidity, "pressure": pressure, "weather_description": weather_description, "temp_c": round(temp_c), "temp_f": round(temp_f), "weather_icon": weather_icon},
        )
    else:
        # User is not authenticated, return the login page
        return templates.TemplateResponse("login.html", {"request": request, "error_message": "Invalid credentials"})