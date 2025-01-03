from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
import os

import boto3

cognito_client = boto3.client('cognito-idp',
                              os.environ.get('region', 'eu-central-1'))
CUP_ID = os.environ.get('cup_id')
CLIENT_ID = os.environ.get('cup_client_id')
_LOG = get_logger('ApiHandler-handler')


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(event, context):
        
        def signup(email, password):
            custom_attr = [{
                'Name': 'email',
                'Value': email
            }]
            try:
                cognito_client.sign_up(
                    ClientId=CLIENT_ID,
                    Username=email,
                    Password=password,
                    UserAttributes=custom_attr)
                cognito_client.admin_confirm_sign_up(
                    UserPoolId=CUP_ID, Username=email)
            except Exception as e:
                print(str(e))
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps({'message': f'Cannot create user {email}.'})
                }

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({'message': f'User {email} was created.'})
            }


        def signin(email, password):
            auth_params = {
                'USERNAME': email,
                'PASSWORD': password
            }
            auth_result = cognito_client.admin_initiate_auth(
                UserPoolId=CUP_ID,
                ClientId=CLIENT_ID,
                AuthFlow='ADMIN_USER_PASSWORD_AUTH', AuthParameters=auth_params)

            if auth_result:
                id_token = auth_result['AuthenticationResult']['IdToken']
            else:
                id_token = None

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps(id_token)
            }
        print(event)
        body = json.loads(event['body'])
        request_path = event['resource']
        email = body.get('email')
        password = body.get('password')

        if request_path == '/signin':
            return signin(email, password)
        elif request_path == '/signup':
            return signup(email, password)
        else:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({'message': 'Unknown request path'})
            }

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.handle_request(event=event, context=context)

