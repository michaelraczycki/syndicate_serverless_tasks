from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('SqsHandler-handler')

class SqsHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        for record in event.get('Records', []):
            message_body = record.get('body', 'No body')
            _LOG.info(f"Received SQS message: {message_body}")
        return 200

HANDLER = SqsHandler()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
