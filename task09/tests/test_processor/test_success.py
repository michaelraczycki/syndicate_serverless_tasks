from unittest.mock import patch, MagicMock
from tests.test_processor import ProcessorLambdaTestCase
from src.lambdas.processor.handler import lambda_handler

class TestSuccess(ProcessorLambdaTestCase):
    @patch("requests.get")
    @patch("boto3.resource")
    def test_success(self, mock_boto_resource, mock_requests_get):
        # Mock requests response
        mock_requests_get.return_value.json.return_value = {
            "elevation": 10,
            "generationtime_ms": 12.34,
            "hourly": {
                "temperature_2m": [1.2, 3.4],
                "time": ["2025-01-02T00:00", "2025-01-02T01:00"]
            },
            "hourly_units": {
                "temperature_2m": "°C",
                "time": "iso8601"
            },
            "latitude": 52.52,
            "longitude": 13.419998,
            "timezone": "GMT",
            "timezone_abbreviation": "GMT",
            "utc_offset_seconds": 0
        }

        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table

        # Invoke the lambda handler
        response = lambda_handler({}, {})

        # Verify
        self.assertEqual(response, 200)
        mock_requests_get.assert_called_once()
        mock_table.put_item.assert_called_once()
