from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
from commons.exception import ApplicationException


_LOG = get_logger('HelloWorld-handler')

class HelloWorld(AbstractLambda):

    def validate_request(self, event) -> None:
        """
        Validate the incoming request. Raise an exception for invalid requests.
        """
        method = event.get('httpMethod') or \
                event.get('requestContext', {}).get('http', {}).get('method', 'UNKNOWN')
        path = event.get('rawPath') or \
            event.get('requestContext', {}).get('http', {}).get('path', 'UNKNOWN')


        _LOG.info(f"Validating request with method: {method}, path: {path}")

        if method == 'GET' and path == '/hello':
            return

        error_message = f"Bad request syntax or unsupported method. Request path: {path}. HTTP method: {method}"
        _LOG.error(error_message)
        raise ApplicationException(code=400, content=error_message)

    def handle_request(self, event, context):
        """
        Handle incoming requests. If valid, return a 200 response.
        """
        self.validate_request(event)

        _LOG.info("Valid request. Returning 200 response.")
        return {
            'statusCode': 200,
            'body': {
                'message': 'Hello from Lambda'
            }
        }


HANDLER = HelloWorld()

def lambda_handler(event, context):
    """
    The main entry point for the AWS Lambda function.
    """
    try:
        _LOG.info(f"Received event: {event}")
        response = HANDLER.handle_request(event=event, context=context)
        _LOG.info(f"Response: {response}")
        return response
    except ApplicationException as e:
        _LOG.error(f"ApplicationException occurred: {e.content}")
        return {
            'statusCode': e.code,
            'body': {
                'message': e.content
            }
        }
    except Exception as e:
        _LOG.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'message': "An internal server error occurred."
            }
        }
