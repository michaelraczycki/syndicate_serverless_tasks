from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('SnsHandler-handler')


class SnsHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        for record in event.get('Records', []):
            try:
                message = record['Sns']['Message']
                _LOG.info(f"Received SNS message: {message}")
            except KeyError as e:
                _LOG.error(f"Missing expected key in the record: {e}")
        return 200
    

HANDLER = SnsHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
