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

from unittest.mock import ANY

class TestAuditProducer(AuditProducerLambdaTestCase):

    pass