import os
import uuid
from datetime import datetime
import boto3

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('AuditProducer-handler')

dynamodb = boto3.resource('dynamodb')
AUDIT_TABLE_NAME = os.environ.get('target_table', 'Audit')


class AuditProducer(AbstractLambda):

    def validate_request(self, event) -> dict:
        return event

    def handle_request(self, event, context):
        """
        Processes DynamoDB stream events to log changes into an 'Audit' table.
        """
        audit_table = dynamodb.Table(AUDIT_TABLE_NAME)
        _LOG.info(f"Starting handling: event: {event}, context: {context}")
        records = event.get('Records', [])
        if not records:
            _LOG.debug("No records to process.")
            return 200
        
        for record in records:
            try:
                event_name = record.get('eventName')
                dynamodb_data = record.get('dynamodb', {})
                _LOG.info(f"Processing event: {event_name}, DynamoDB data: {dynamodb_data}")
                
                # Convert the key
                keys = dynamodb_json_to_dict(dynamodb_data.get('Keys', {}))
                item_key = keys.get('key')  # Configuration item key
                if not item_key:
                    _LOG.error(f"Missing 'key' attribute in record keys: {keys}")
                    continue

                current_time = datetime.now().isoformat()

                # Handle INSERT event
                if event_name == 'INSERT':
                    new_image = dynamodb_json_to_dict(dynamodb_data.get('NewImage', {}))
                    _LOG.info(f"NewImage: {new_image}")
                    audit_item = {
                        "id": str(uuid.uuid4()),
                        "itemKey": item_key,
                        "modificationTime": current_time,
                        "newValue": {
                            "key": new_image.get('key'),
                            "value": new_image.get('value')
                        }
                    }
                    audit_table.put_item(Item=audit_item)
                    _LOG.info(f"INSERT event processed for key={item_key}, audit_item={audit_item}")

                # Handle MODIFY event
                elif event_name == 'MODIFY':
                    new_image = dynamodb_json_to_dict(dynamodb_data.get('NewImage', {}))
                    old_image = dynamodb_json_to_dict(dynamodb_data.get('OldImage', {}))

                    for attr, new_val in new_image.items():
                        old_val = old_image.get(attr)
                        if old_val != new_val:
                            audit_item = {
                                "id": str(uuid.uuid4()),
                                "itemKey": item_key,
                                "modificationTime": current_time,
                                "updatedAttribute": attr,
                                "oldValue": old_val,
                                "newValue": new_val
                            }
                            audit_table.put_item(Item=audit_item)
                            _LOG.info(f"MODIFY event processed for key={item_key}, attribute={attr}, audit_item={audit_item}")

            except Exception as e:
                _LOG.error(f"Failed to process record: {record}. Error: {e}")
                continue

        return 200


HANDLER = AuditProducer()


def lambda_handler(event, context):
    _LOG.info(f"Lambda invocation started. event:{event}, context:{context}")
    try:
        return HANDLER.handle_request(event=event, context=context)
    except Exception as e:
        _LOG.error(msg=f"error happened: {e}")


def dynamodb_json_to_dict(dynamodb_json):
    """
    Converts DynamoDB JSON structure into a standard Python dict.
    Handles data types such as String (S), Number (N), Map (M), and List (L).
    """
    if isinstance(dynamodb_json, dict):
        result = {}
        for key, value in dynamodb_json.items():
            if isinstance(value, dict):
                if "S" in value:  # String
                    result[key] = value["S"]
                elif "N" in value:  # Number
                    result[key] = int(value["N"]) if "." not in value["N"] else float(value["N"])
                elif "M" in value:  # Map
                    result[key] = dynamodb_json_to_dict(value["M"])
                elif "L" in value:  # List
                    result[key] = [dynamodb_json_to_dict(item) for item in value["L"]]
            else:
                result[key] = value
        return result
    elif isinstance(dynamodb_json, list):
        return [dynamodb_json_to_dict(item) for item in dynamodb_json]
    else:
        return dynamodb_json
