#debug script for testing json_to_dict function
dynamodb_data = {'ApproximateCreationDateTime': 1734352190.0, 'Keys': {'key': {'S': 'CACHE_TTL_SEC'}}, 'NewImage': {'value': {'S': '3600'}, 'key': {'S': 'CACHE_TTL_SEC'}}, 'SequenceNumber': '1500000000056028908020', 'SizeBytes': 41, 'StreamViewType': 'NEW_AND_OLD_IMAGES'}
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
new_image = dynamodb_json_to_dict(dynamodb_data.get("NewImage"))
print(new_image.get("key"))