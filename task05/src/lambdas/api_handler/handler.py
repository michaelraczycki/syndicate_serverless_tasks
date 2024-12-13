import json
import os
import uuid
from datetime import datetime

import boto3

from commons.abstract_lambda import AbstractLambda
from commons.log_helper import get_logger

_LOG = get_logger('ApiHandler-handler')


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        # Example validation:
        # if "principalId" not in event or "content" not in event:
        #     raise ValueError("Invalid request")
        pass

    def handle_request(self, event, context):
        _LOG.info(msg=f'event:{event}, context:{context}')
        
        # Extract needed fields from event
        principal_id = event.get("principalId")
        body_content = event.get("content", {})

        # Construct the item to be saved to DynamoDB
        obj = {
            "id": str(uuid.uuid4()),
            "principalId": principal_id,
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "body": body_content
        }

        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('region', 'eu-central-1'))
        table_name = os.environ.get('table_name', 'Events')
        _LOG.info(msg=f"trying to get table: {table_name}")

        table = dynamodb.Table(table_name)
        table.put_item(Item=obj)

        # Return the desired response
        response = {
            "statusCode": 201,
            "event": obj
        }

        return {
            "statusCode": response["statusCode"],
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(response, indent=4)
        }
    

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
