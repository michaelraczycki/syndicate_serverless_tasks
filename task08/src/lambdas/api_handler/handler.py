# src/lambdas/api_handler/handler.py

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import requests

_LOG = get_logger('ApiHandler-handler')

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


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        return {}

    def handle_request(self, event, context):
        """
        Handle the incoming event and fetch weather data
        """
        latitude = float(50.4375)
        longitude = float(30.5)

        # Create an instance of the WeatherSDK
        weather_sdk = WeatherSDK(latitude, longitude)
        
        # Get weather data
        weather_data = weather_sdk.get_weather()

        if 'error' in weather_data:
            _LOG.error(f"Error fetching weather: {weather_data['error']}")
            return {
                'statusCode': 500,
                'body': f"Error: {weather_data['error']}"
            }

        # Explicitly structure the hourly data to match the expected format
        hourly_data = weather_data.get('hourly', {})
        structured_hourly = {
            'time': hourly_data.get('time', []),
            'temperature_2m': hourly_data.get('temperature_2m', []),
            'relative_humidity_2m': hourly_data.get('relative_humidity_2m', []),
            'wind_speed_10m': hourly_data.get('wind_speed_10m', []),
        }

        # Return the structured response
        return {
            'statusCode': 200,
            'body': {
                'latitude': weather_data.get('latitude'),
                'longitude': weather_data.get('longitude'),
                'hourly': structured_hourly
            }
        }

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.handle_request(event=event, context=context)
