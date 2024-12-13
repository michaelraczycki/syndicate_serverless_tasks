from unittest.mock import patch, MagicMock
from tests.test_api_handler import ApiHandlerLambdaTestCase


class TestSuccess(ApiHandlerLambdaTestCase):

    @patch("boto3.resource")
    def test_success(self, mock_boto_resource):
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        event = {
            "principalId": 1,
            "content": {"name": "John", "surname": "Doe"}
        }
        context = {}

        response = self.HANDLER.handle_request(event, context)

        self.assertEqual(response["statusCode"], 201)
        self.assertIn("event", response)
        self.assertIn("id", response["event"])
        self.assertIn("principalId", response["event"])
        self.assertIn("createdAt", response["event"])
        self.assertIn("body", response["event"])

        self.assertEqual(response["event"]["principalId"], 1)
        self.assertEqual(response["event"]["body"], {"name": "John", "surname": "Doe"})

        put_item_args = mock_table.put_item.call_args[1]["Item"]
        self.assertIn("id", put_item_args)
        self.assertIn("principalId", put_item_args)
        self.assertIn("createdAt", put_item_args)
        self.assertIn("body", put_item_args)

        self.assertEqual(put_item_args["principalId"], 1)
        self.assertEqual(put_item_args["body"], {"name": "John", "surname": "Doe"})
