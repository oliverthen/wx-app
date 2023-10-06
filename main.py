from fastapi import FastAPI
import requests

app = FastAPI()

key_api = '7bde4586e85a32fd9b24b872e8506e30'

@app.get("/")
def root():
	lat = input("Enter latitude: ")
	lon = input("Enter longitude: ")

	url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={key_api}'

	response = requests.get(url)
	data = response.json()

	# if response.status_code == 200:
	# 	data = response.json()
	# 	# temp = data['current']['temp']
	# 	# desc = data['curent']['weather'][descrip tion]
	# else:
	# 	print('Error fetching weather data')

	return data['current']['temp']

# @app.get("/{city_id}")
# async def root():
# 	return {"message": "Weather App"}