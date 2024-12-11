import unittest
from unittest.mock import patch
from tests.test_sqs_handler import SqsHandlerLambdaTestCase

class TestSuccess(SqsHandlerLambdaTestCase):

    @patch('commons.log_helper._LOG')
    def test_success(self, mock_logger):
        event = {
            "Records": [
                {"body": "Message1"},
                {"body": "Message2"}
            ]
        }
        result = self.HANDLER.handle_request(event, {})
        self.assertEqual(result, 200)
        
        # Verify that both messages have been logged
        mock_logger.info.assert_any_call("Received SQS message: Message1")
        mock_logger.info.assert_any_call("Received SQS message: Message2")
