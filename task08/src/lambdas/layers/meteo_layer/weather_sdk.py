import requests

class WeatherSDK:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'current': 'temperature_2m,wind_speed_10m',
            'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m',
        }

    def get_weather(self):
        try:
            response = requests.get(self.base_url, params=self.params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
