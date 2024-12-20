# src/lambdas/api_handler/handler.py

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
from src.lambdas.layers.meteo_layer.weather_sdk import WeatherSDK


_LOG = get_logger('ApiHandler-handler')


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        # You can add logic here to validate incoming requests if needed
        return {}

    def handle_request(self, event, context):
        """
        Handle the incoming event and fetch weather data
        """
        # Extract latitude and longitude from the query parameters (defaults if not present)
        latitude = float(event['queryStringParameters'].get('latitude', 50.4375))  # Default to 50.4375
        longitude = float(event['queryStringParameters'].get('longitude', 30.5))  # Default to 30.5

        # Create an instance of the WeatherSDK class
        weather_sdk = WeatherSDK(latitude, longitude)
        
        # Get weather data
        weather_data = weather_sdk.get_weather()

        # Return weather data or a message if there's an error
        if 'error' in weather_data:
            _LOG.error(f"Error fetching weather: {weather_data['error']}")
            return {
                'statusCode': 500,
                'body': f"Error: {weather_data['error']}"
            }
        
        return {
            'statusCode': 200,
            'body': weather_data  # Return the weather data as JSON
        }
    

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.handle_request(event=event, context=context)
