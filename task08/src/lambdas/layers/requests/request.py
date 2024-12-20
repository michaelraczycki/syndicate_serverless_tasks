import requests

class WeatherSDK:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'current': 'temperature_2m,wind_speed_10m',  # Current weather data
            'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m',  # Hourly forecast data
        }

    def get_weather(self):
        try:
            response = requests.get(self.base_url, params=self.params)
            response.raise_for_status()  # Raise an error for bad status codes
            return response.json()  # Return the parsed JSON response
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
