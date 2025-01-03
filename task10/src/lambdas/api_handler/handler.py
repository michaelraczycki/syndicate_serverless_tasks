from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
import os
import uuid
import boto3
from datetime import datetime
import random

_LOG = get_logger('ApiHandler-handler')

cognito_client = boto3.client(
    'cognito-idp',
    region_name=os.environ.get('region', 'eu-central-1')
)

# Environment variables set in Lambda configuration
CUP_ID = os.environ.get('cup_id')
CLIENT_ID = os.environ.get('cup_client_id')
tables_name = os.environ.get("tables_table")
reservations_name = os.environ.get("reservations_table")
# DynamoDB setup
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('region', 'eu-central-1')
)
tables_table = dynamodb.Table(tables_name)
reservations_table = dynamodb.Table(reservations_name)


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        # You can implement additional request validation here if needed
        pass

    def handle_request(self, event, context):
        """
        Main dispatch for the API endpoints.
        """
        _LOG.info("Lambda event: %s", json.dumps(event))
        method = event.get('httpMethod')
        path = event.get('resource')
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except Exception as e:
                _LOG.error("Error parsing request body: %s", str(e))
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "Invalid JSON input."})
                }

        _LOG.info("Received request. Path: %s, Method: %s", path, method)

        # Signup
        if path == '/signup' and method == 'POST':
            return self.signup(body)

        # Signin
        if path == '/signin' and method == 'POST':
            return self.signin(body)

        # Tables: GET all
        if path == '/tables' and method == 'GET':
            return self.get_tables()

        # Tables: POST (create)
        if path == '/tables' and method == 'POST':
            return self.create_table(body)

        # Tables: GET one (assuming /tables/{tableId} is configured in the API)
        if path == '/tables/{tableId}' and method == 'GET':
            table_id = event.get('pathParameters', {}).get('tableId')
            return self.get_table_by_id(table_id)

        # Reservations: GET all
        if path == '/reservations' and method == 'GET':
            return self.get_reservations()

        # Reservations: POST (create)
        if path == '/reservations' and method == 'POST':
            return self.create_reservation(body)

        # Fallback if no matching route
        _LOG.warning("No matching route found for path: %s, method: %s", path, method)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Unsupported path {path} or method {method}"})
        }

    def signup(self, body: dict):
        """ Sign up a new user in Cognito and auto-confirm them. """
        email = body.get('email')
        password = body.get('password')
        _LOG.info("Preparing signup. Email: %s", email)

        if not email or not password:
            _LOG.error("Signup failed. Missing email or password.")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Missing email or password in signup.'})
            }

        try:
            _LOG.info("Attempting sign_up with Cognito. Email: %s", email)
            cognito_client.sign_up(
                ClientId=CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[{'Name': 'email', 'Value': email}]
            )
            _LOG.info("Sign_up call succeeded. Now confirming sign_up in admin mode.")
            cognito_client.admin_confirm_sign_up(
                UserPoolId=CUP_ID,
                Username=email
            )
        except Exception as e:
            _LOG.error(f"Sign up error for email '{email}': {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    'message': f'Cannot create user {email}. Error: {str(e)}'
                })
            }

        _LOG.info("User %s was created and confirmed successfully.", email)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({'message': f'User {email} was created.'})
        }

    def signin(self, body: dict):
        """ Sign in a user and return their ID token as 'accessToken'. """
        email = body.get('email')
        password = body.get('password')
        _LOG.info("Preparing signin. Email: %s", email)

        if not email or not password:
            _LOG.error("Signin failed. Missing email or password.")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Missing email or password in signin.'})
            }

        try:
            _LOG.info("Attempting admin_initiate_auth for email: %s", email)
            auth_result = cognito_client.admin_initiate_auth(
                UserPoolId=CUP_ID,
                ClientId=CLIENT_ID,
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )

            _LOG.info("admin_initiate_auth response: %s", auth_result)

            if auth_result and 'AuthenticationResult' in auth_result:
                id_token = auth_result['AuthenticationResult'].get('IdToken')
                # Return the ID token under the key "accessToken" per requirements
                _LOG.info("Signin success for user: %s", email)
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"accessToken": id_token})
                }
            else:
                _LOG.error("Signin failed. AuthenticationResult missing or invalid.")
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({'message': 'Unable to authenticate user.'})
                }
        except Exception as e:
            _LOG.error(f"Sign in error for email '{email}': {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Invalid login.'})
            }

    def get_tables(self):
        """
        Return a list of all tables.
        {
            "tables": [
                {
                    "id": ...,
                    "number": ...,
                    "places": ...,
                    "isVip": ...,
                    "minOrder": ...
                },
                ...
            ]
        }
        """
        _LOG.info("Fetching all tables from DynamoDB.")
        try:
            response = tables_table.scan()
            items = response.get('Items', [])
            _LOG.info("Tables scan response: %s", items)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"tables": items})
            }
        except Exception as e:
            _LOG.error(f"Error fetching tables: {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Unable to retrieve tables.'})
            }

    def create_table(self, body: dict):
        """
        Create a new table item in DynamoDB. The request body should have:
        {
            "id": int,
            "number": int,
            "places": int,
            "isVip": bool,
            "minOrder": optional int
        }
        """
        _LOG.info("Request to create a new table. Body: %s", body)
        table_id = body.get('id')
        table_number = body.get('number')
        places = body.get('places')
        is_vip = body.get('isVip')
        min_order = body.get('minOrder', None)

        if table_id is None or table_number is None or places is None or is_vip is None:
            _LOG.error("Missing required fields for table creation.")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Missing required fields for table creation.'})
            }

        try:
            item = {
                'id': int(table_id),
                'number': int(table_number),
                'places': int(places),
                'isVip': bool(is_vip)
            }
            if min_order is not None:
                item['minOrder'] = int(min_order)

            tables_table.put_item(Item=item)
            _LOG.info("Table created successfully with id: %d", table_id)

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"id": table_id})
            }
        except Exception as e:
            _LOG.error(f"Error creating table: {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Unable to create the table.'})
            }

    def get_table_by_id(self, table_id):
        """ Fetch a single table item by its ID. """
        _LOG.info("Fetching table by id: %s", table_id)
        if not table_id:
            _LOG.error("Missing tableId in path parameters.")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Missing tableId in path parameters.'})
            }

        try:
            response = tables_table.get_item(Key={'id': int(table_id)})
            item = response.get('Item')
            if not item:
                _LOG.error("Table not found with id: %s", table_id)
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({'message': f'Table with id {table_id} not found.'})
                }

            _LOG.info("Retrieved table data: %s", item)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(item)
            }
        except Exception as e:
            _LOG.error(f"Error fetching table by ID {table_id}: {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': f'Unable to retrieve table {table_id}.'})
            }

    def get_reservations(self):
        """
        Return a list of all reservations.
        {
            "reservations": [
                {
                    "tableNumber": int,
                    "clientName": string,
                    "phoneNumber": string,
                    "date": string (yyyy-MM-dd),
                    "slotTimeStart": string (HH:MM),
                    "slotTimeEnd": string (HH:MM)
                },
                ...
            ]
        }
        """
        _LOG.info("Fetching all reservations from DynamoDB.")
        try:
            response = reservations_table.scan()
            items = response.get('Items', [])
            _LOG.info("Reservations scan response: %s", items)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"reservations": items})
            }
        except Exception as e:
            _LOG.error(f"Error fetching reservations: {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Unable to retrieve reservations.'})
            }

    def create_reservation(self, body: dict):
        """
        Create a new reservation item in DynamoDB.
        {
            "tableNumber": int,
            "clientName": string,
            "phoneNumber": string,
            "date": string (yyyy-MM-dd),
            "slotTimeStart": string (HH:MM),
            "slotTimeEnd": string (HH:MM)
        }
        Returns: { "reservationId": <uuidv4> }
        """
        _LOG.info("Request to create a new reservation. Body: %s", body)
        table_number = body.get('tableNumber')
        client_name = body.get('clientName')
        phone_number = body.get('phoneNumber')
        date_val = body.get('date')
        slot_start = body.get('slotTimeStart')
        slot_end = body.get('slotTimeEnd')

        # Basic validation
        if (
            table_number is None or
            not client_name or
            not phone_number or
            not date_val or
            not slot_start or
            not slot_end
        ):
            _LOG.error("Missing required reservation fields.")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Missing required reservation fields.'})
            }

        # Generate a numeric "id" to match table schema "hash_key_type": "N"
        # but also return a separate string reservationId (UUID) to the client
        reservation_id_str = str(uuid.uuid4())
        numeric_id = random.randint(1, 999999999)

        try:
            item = {
                'id': numeric_id,
                'reservationId': reservation_id_str,
                'tableNumber': int(table_number),
                'clientName': client_name,
                'phoneNumber': phone_number,
                'date': date_val,
                'slotTimeStart': slot_start,
                'slotTimeEnd': slot_end
            }

            reservations_table.put_item(Item=item)
            _LOG.info("Reservation created. ID: %d, UUID: %s", numeric_id, reservation_id_str)

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"reservationId": reservation_id_str})
            }
        except Exception as e:
            _LOG.error(f"Error creating reservation: {str(e)}")
            _LOG.exception(e)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({'message': 'Unable to create reservation.'})
            }


HANDLER = ApiHandler()


def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    """
    _LOG.info("Entered lambda_handler with event: %s", json.dumps(event))
    return HANDLER.handle_request(event, context)
