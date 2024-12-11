from unittest.mock import patch
from unittest import TestCase
from src.lambdas.sns_handler.handler import HANDLER

class TestSuccess(TestCase):

    @patch('src.lambdas.sns_handler.handler._LOG')
    def test_success(self, mock_logger):
        event = {
            "Records": [
                {
                    "Sns": {
                        "Message": "Message1"
                    }
                },
                {
                    "Sns": {
                        "Message": "Message2"
                    }
                }
            ]
        }

        result = HANDLER.handle_request(event, {})
        self.assertEqual(result, 200)
        
        mock_logger.info.assert_any_call("Received SNS message: Message1")
        mock_logger.info.assert_any_call("Received SNS message: Message2")
        