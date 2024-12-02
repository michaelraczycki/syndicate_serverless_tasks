from commons.exception import ApplicationException  # Adjusted import
from tests.test_hello_world import HelloWorldLambdaTestCase

class TestHelloWorldLambda(HelloWorldLambdaTestCase):

    def test_success(self):
        event = {
            "httpMethod": "GET",
            "rawPath": "/hello"
        }
        response = self.HANDLER.handle_request(event, dict())
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["message"], "Hello from Lambda")

    def test_invalid_method(self):
        event = {
            "httpMethod": "POST",
            "rawPath": "/hello"
        }
        with self.assertRaises(ApplicationException) as context:
            self.HANDLER.handle_request(event, dict())
        exception = context.exception
        self.assertEqual(exception.code, 400)
        self.assertIn("Bad request syntax or unsupported method", exception.content)
        self.assertIn("HTTP method: POST", exception.content)

    def test_invalid_path(self):
        event = {
            "httpMethod": "GET",
            "rawPath": "/invalid_path"
        }
        with self.assertRaises(ApplicationException) as context:
            self.HANDLER.handle_request(event, dict())
        exception = context.exception
        self.assertEqual(exception.code, 400)
        self.assertIn("Bad request syntax or unsupported method", exception.content)
        self.assertIn("Request path: /invalid_path", exception.content)
