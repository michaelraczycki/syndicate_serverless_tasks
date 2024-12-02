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
            "statusCode": 200,
            "message": "Hello from Lambda"
        }


HANDLER = HelloWorld()

def lambda_handler(event, context):
    try:
        response = HANDLER.handle_request(event, context)
        _LOG.info(f"wrong path or method - response to return: {response}")
        return response
    except ApplicationException as e:
        _LOG.info(f"wrong path or method: statusCode:{e.code}, message:{e.content}")
        response = {
            "statusCode": e.code,
            "message": e.content
        }
        _LOG.info(f"wrong path or method - response to return: {response}")
        return response