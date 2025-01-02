import os
import uuid
import boto3
import requests
from decimal import Decimal

from aws_xray_sdk.core import patch_all

patch_all()

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('Processor-handler')

class Processor(AbstractLambda):
    def validate_request(self, event) -> dict:
        # You can implement some event validation if needed
        return event

    def handle_request(self, event, context):
        self.validate_request(event)
        _LOG.info(f"Received event: '{event}', processing.")
        url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
        response = requests.get(url)
        forecast_data = response.json()

        table_name = os.environ.get("target_table", "Weather")
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        _LOG.info(f"found table: {table} for write")

        # Convert all float types to Decimal
        def convert_to_decimal(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, list):
                return [convert_to_decimal(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_decimal(v) for k, v in obj.items()}
            return obj

        # Convert forecast_data to match DynamoDB requirements
        item = {
            "id": str(uuid.uuid4()),
            "forecast": convert_to_decimal({
                "elevation": forecast_data.get("elevation"),
                "generationtime_ms": forecast_data.get("generationtime_ms"),
                "hourly": {
                    "temperature_2m": forecast_data["hourly"].get("temperature_2m", []),
                    "time": forecast_data["hourly"].get("time", []),
                },
                "hourly_units": {
                    "temperature_2m": forecast_data["hourly_units"].get("temperature_2m"),
                    "time": forecast_data["hourly_units"].get("time"),
                },
                "latitude": forecast_data.get("latitude"),
                "longitude": forecast_data.get("longitude"),
                "timezone": forecast_data.get("timezone"),
                "timezone_abbreviation": forecast_data.get("timezone_abbreviation"),
                "utc_offset_seconds": forecast_data.get("utc_offset_seconds"),
            })
        }

        _LOG.info(f"prepared an item to be saved: {item}")
        try:
            table.put_item(Item=item)
            return 200
        except Exception as e:
            _LOG.error(f"something went wrong, received error: {e}")
            return 400

HANDLER = Processor()

def lambda_handler(event, context):
    return HANDLER.handle_request(event=event, context=context)
