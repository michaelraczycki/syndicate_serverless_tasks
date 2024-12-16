import json
import os
import uuid
from datetime import datetime

import boto3

from commons.abstract_lambda import AbstractLambda
from commons.log_helper import get_logger

_LOG = get_logger('UuidGenerator-handler')

# Initialize S3 client
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('target_bucket', 'uuid-storage')
class UuidGenerator(AbstractLambda):
    def validate_request(self, event) -> dict:
        # Validation logic here if needed
        return {}

    def handle_request(self, event, context):
        """
        Event is triggered by CloudWatch every minute.
        The function generates 10 UUIDs, creates a file, and uploads it to S3.
        """
        _LOG.info("Generating 10 UUIDs...")
        
        # Generate 10 UUIDs
        uuids = [str(uuid.uuid4()) for _ in range(10)]
        
        # Prepare the content for the file
        content = {"ids": uuids}
        file_content = json.dumps(content, indent=4)
        
        # Generate the filename with the current ISO timestamp
        timestamp = datetime.now().isoformat(timespec='milliseconds') + "Z"
        file_name = f"{timestamp}.json"
        
        _LOG.info(f"Uploading file '{file_name}' to S3 bucket '{S3_BUCKET}'...")
        
        # Upload the file to the S3 bucket
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=file_name,
                Body=file_content,
                ContentType='application/json'
            )
            _LOG.info(f"File '{file_name}' successfully uploaded.")
        except Exception as e:
            _LOG.error(f"Failed to upload file: {str(e)}")
            raise
        
        return {"statusCode": 200, "body": "Successfully generated UUIDs and uploaded to S3."}

HANDLER = UuidGenerator()

def lambda_handler(event, context):
    return HANDLER.handle_request(event=event, context=context)
