import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid
from src.lambdas.audit_producer.handler import AuditProducer, dynamodb_json_to_dict


class AuditProducerLambdaTestCase(unittest.TestCase):

    def setUp(self):
        self.HANDLER = AuditProducer()
        self.dynamodb_mock = patch('src.lambdas.audit_producer.handler.dynamodb').start()
        self.addCleanup(patch.stopall)

    def mock_dynamodb_table(self):
        table_mock = MagicMock()
        self.dynamodb_mock.resource.return_value.Table.return_value = table_mock
        return table_mock

from unittest.mock import ANY, call

class TestAuditProducer(AuditProducerLambdaTestCase):

    @patch('src.lambdas.audit_producer.handler._LOG')
    def test_insert_event(self, log_mock):
        table_mock = self.mock_dynamodb_table()
        patch('uuid.uuid4', return_value=uuid.UUID(int=0)).start()

        new_image = {
            "key": {"S": "123"},
            "name": {"S": "TestName"},
        }
        event = {
            "Records": [
                {
                    "eventName": "INSERT",
                    "dynamodb": {
                        "NewImage": new_image
                    }
                }
            ]
        }

        response = self.HANDLER.handle_request(event, None)

        self.assertEqual(response, 200)

        # Validate that the debug log was called with the correct key and values
        log_mock.debug.assert_called()
        logged_call = log_mock.debug.call_args[0][0]
        self.assertIn("INSERT event for key=123, creating audit:", logged_call)

        # Validate the logged item without comparing the timestamp
        logged_item = log_mock.debug.call_args[0][0].split("creating audit: ")[1]
        expected_item = {
            "id": "00000000-0000-0000-0000-000000000000",
            "itemKey": "123",
            "modificationTime": ANY,  # Allow any timestamp value
            "newValue": dynamodb_json_to_dict(new_image)
        }
        logged_item_dict = eval(logged_item)  # Convert logged string to dictionary
        self.assertEqual(logged_item_dict["id"], expected_item["id"])
        self.assertEqual(logged_item_dict["itemKey"], expected_item["itemKey"])
        self.assertEqual(logged_item_dict["newValue"], expected_item["newValue"])

    @patch('src.lambdas.audit_producer.handler._LOG')
    def test_modify_event(self, log_mock):
        table_mock = self.mock_dynamodb_table()
        patch('uuid.uuid4', return_value=uuid.UUID(int=0)).start()

        new_image = {
            "key": {"S": "123"},
            "name": {"S": "NewName"},
        }
        old_image = {
            "key": {"S": "123"},
            "name": {"S": "OldName"},
        }
        event = {
            "Records": [
                {
                    "eventName": "MODIFY",
                    "dynamodb": {
                        "NewImage": new_image,
                        "OldImage": old_image
                    }
                }
            ]
        }

        response = self.HANDLER.handle_request(event, None)

        self.assertEqual(response, 200)

        # Validate that the debug log was called
        log_mock.debug.assert_called()
        logged_call = log_mock.debug.call_args[0][0]

        # Extract the logged audit message
        self.assertTrue("MODIFY event for key=123, attribute=name, audit=" in logged_call)
        logged_item = logged_call.split("audit=")[1]

        # Validate the logged item as a dictionary
        expected_item = {
            "id": "00000000-0000-0000-0000-000000000000",
            "itemKey": "123",
            "modificationTime": ANY,  # Allow any timestamp value
            "updatedAttribute": "name",
            "oldValue": "OldName",
            "newValue": "NewName"
        }
        logged_item_dict = eval(logged_item)  # Convert logged string to dictionary
        self.assertEqual(logged_item_dict["id"], expected_item["id"])
        self.assertEqual(logged_item_dict["itemKey"], expected_item["itemKey"])
        self.assertEqual(logged_item_dict["updatedAttribute"], expected_item["updatedAttribute"])
        self.assertEqual(logged_item_dict["oldValue"], expected_item["oldValue"])
        self.assertEqual(logged_item_dict["newValue"], expected_item["newValue"])



    def test_dynamodb_json_to_dict(self):
        dynamodb_json = {
            "key": {"S": "123"},
            "value": {"N": "456"}
        }

        expected_dict = {
            "key": "123",
            "value": 456
        }

        self.assertEqual(dynamodb_json_to_dict(dynamodb_json), expected_dict)


if __name__ == "__main__":
    unittest.main()
