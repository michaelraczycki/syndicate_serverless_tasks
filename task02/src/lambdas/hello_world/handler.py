from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
from commons.exception import ApplicationException


_LOG = get_logger('HelloWorld-handler')

class HelloWorld(AbstractLambda):

    def validate_request(self, event) -> None:
        method = event.get('httpMethod') or \
                 event.get('requestContext', {}).get('http', {}).get('method', 'UNKNOWN')
        path = event.get('rawPath') or \
               event.get('requestContext', {}).get('http', {}).get('path', 'UNKNOWN')

        _LOG.info(f"Validating request with method: {method}, path: {path}")

        if method == 'GET' and path == '/hello':
            return

        raise ApplicationException(
            code=400,
            content=f"Bad request syntax or unsupported method. Request path: {path}. HTTP method: {method}"
        )

    def handle_request(self, event, context):
        self.validate_request(event)
        return {
            'statusCode': 200,
            'message': 'Hello from Lambda'
        }


HANDLER = HelloWorld()

def lambda_handler(event, context):
    try:
        _LOG.info(f"Received event: {event}")
        response = HANDLER.handle_request(event, context)
        _LOG.info(f"Response: {response}")
        return response
    except ApplicationException as e:
        _LOG.error(f"ApplicationException occurred: {e.content}")
        return {
            'statusCode': e.code,
            'message': e.content
        }
    except Exception as e:
        _LOG.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'message': "An internal server error occurred."
        }
