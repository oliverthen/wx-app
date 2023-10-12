from fastapi import FastAPI, Form, Request
from decouple import config
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

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

