import os
import uuid
from datetime import datetime
import boto3

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('AuditProducer-handler')

dynamodb = boto3.resource('dynamodb')
AUDIT_TABLE_NAME = os.environ.get('AUDIT_TABLE_NAME', 'Audit')


class AuditProducer(AbstractLambda):

    def validate_request(self, event) -> dict:
        # No explicit request validation needed for stream events
        return event

    def handle_request(self, event, context):
        """
        The event is triggered by a DynamoDB stream on the 'Configuration' table.
        Records in the event show changes (INSERT, MODIFY, REMOVE) on items in the 
        'Configuration' table. This handler extracts changes and logs them into an 
        'Audit' table.

        For INSERT:
          - Creates an audit record with the new item's value.

        For MODIFY:
          - Compares old and new values.
          - For each changed attribute, creates an audit record indicating old and new values.
        
        After processing all records, returns HTTP 200.
        """

        audit_table = dynamodb.Table(AUDIT_TABLE_NAME)
        current_time = datetime.utcnow().isoformat() + 'Z'  # Example: 2024-01-01T00:00:00.000Z

        records = event.get('Records', [])
        if not records:
            _LOG.debug("No records to process.")
            return 200

        for record in records:
            event_name = record['eventName']
            if event_name == 'INSERT':
                # New item created
                new_image = record['dynamodb']['NewImage']
                new_value = dynamodb_json_to_dict(new_image)
                item_key = new_value['key']

                audit_item = {
                    "id": str(uuid.uuid4()),
                    "itemKey": item_key,
                    "modificationTime": current_time,
                    "newValue": new_value
                }
                _LOG.debug(f"INSERT event for key={item_key}, creating audit: {audit_item}")
                audit_table.put_item(Item=audit_item)

            elif event_name == 'MODIFY':
                new_image = record['dynamodb']['NewImage']
                old_image = record['dynamodb']['OldImage']
                new_dict = dynamodb_json_to_dict(new_image)
                old_dict = dynamodb_json_to_dict(old_image)
                item_key = new_dict['key']

                for attr in new_dict:
                    old_val = old_dict.get(attr)
                    new_val = new_dict.get(attr)
                    if old_val != new_val:
                        audit_item = {
                            "id": str(uuid.uuid4()),
                            "itemKey": item_key,
                            "modificationTime": current_time,
                            "updatedAttribute": attr,
                            "oldValue": old_val,
                            "newValue": new_val
                        }
                        _LOG.debug(f"MODIFY event for key={item_key}, attribute={attr}, audit={audit_item}")
                        audit_table.put_item(Item=audit_item)
            else:
                _LOG.debug(f"Unsupported event type: {event_name}")

        return 200


HANDLER = AuditProducer()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)


def dynamodb_json_to_dict(dynamodb_json):
    """
    Convert a DynamoDB JSON dict from stream to a standard Python dict.
    Supports basic scalar types (S, N) common in this scenario.
    Extend as needed for more complex attribute types.
    """
    result = {}
    for k, v in dynamodb_json.items():
        for dtype, val in v.items():
            if dtype == 'S':
                result[k] = val
            elif dtype == 'N':
                result[k] = int(val)
    return result
