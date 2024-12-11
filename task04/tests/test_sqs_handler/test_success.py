from unittest.mock import patch
from unittest import TestCase
from src.lambdas.sqs_handler.handler import HANDLER

class TestSuccess(TestCase):

    @patch('src.lambdas.sqs_handler.handler._LOG')
    def test_success(self, mock_logger):
        event = {
            "Records": [
                {"body": "Message1"},
                {"body": "Message2"}
            ]
        }
        result = HANDLER.handle_request(event, {})
        self.assertEqual(result, 200)
        
        mock_logger.info.assert_any_call("Received SQS message: Message1")
        mock_logger.info.assert_any_call("Received SQS message: Message2")
