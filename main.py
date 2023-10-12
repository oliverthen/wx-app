from fastapi import FastAPI, Form, Request
from decouple import config
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates")

key_api = config('API_KEY')

@app.get("/", response_class=HTMLResponse)
async def get_coordinates(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_coordinates", response_class=HTMLResponse)
async def process_coordinates(
    request: Request,
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    
    url = f'https://api.openweathermap.org/data/3.0/onecall?lat={str(latitude)}&lon={str(longitude)}&appid={key_api}'

    response = requests.get(url)
    data = response.json()
    
    temp_c = data['current']['temp'] - 273.15
    temp_f = (temp_c * 9/5) + 32
    print("Temp in C is", temp_c)

    return templates.TemplateResponse("weather.html", {"request": request, "temp_c": round(temp_c), "temp_f": round(temp_f)})