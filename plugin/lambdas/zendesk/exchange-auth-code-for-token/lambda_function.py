# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import base64
import json
import os
import time

import boto3
import requests

# Initialize AWS clients
secretsmanager = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    try:
        # Create a sanitized copy of the event for logging only
        import copy

        safe_event = copy.deepcopy(event)

        # Redact sensitive information in body-json
        if "body-json" in safe_event and "code" in safe_event["body-json"]:
            safe_event["body-json"]["code"] = "***REDACTED***"

        # Redact sensitive information in headers (like referer which contains the code)
        if "params" in safe_event and "header" in safe_event["params"] and "referer" in safe_event["params"]["header"]:
            safe_event["params"]["header"]["referer"] = "***REDACTED***"

        print(f"Received event: {safe_event}")

        # Parse the request body
        body = parse_body(event)

        # Get required parameters
        code = body.get("code")
        state = body.get("state")

        # Validate required parameters
        if not code or not state:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Missing Required Parameters",
                        "message": "Please provide code and state",
                        "requiredParameters": ["code", "state"],
                    }
                ),
            }

        # Retrieve state from DynamoDB
        state_data = get_state(state)
        if not state_data:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Invalid State",
                        "message": "The authorization request has expired or is invalid. Please try again.",
                    }
                ),
            }

        # Get client credentials from state
        client_id = state_data.get("clientId")
        client_secret = state_data.get("clientSecret")
        zendesk_subdomain = state_data.get("zendeskSubdomain")

        # Get API Gateway URL for redirect URI
        api_gateway_url = os.environ.get("API_GATEWAY_URL", "")
        redirect_uri = f"{api_gateway_url}zendesk-oauth-callback"

        # Exchange code for token
        token_data = exchange_code_for_token(zendesk_subdomain, client_id, client_secret, code, redirect_uri)

        # Extract the numerical part from the client ID
        client_id = state_data.get("clientId")  # e.g., "amazon-q-business-1750882988"
        unique_id = client_id.split("-")[-1]  # Extract "1750882988"

        # Store token in Secrets Manager
        secret_name = f"qbusiness-zendesk-secret-{zendesk_subdomain}-{unique_id}"
        store_token(secret_name, token_data, zendesk_subdomain)

        # Delete state from DynamoDB
        delete_state(state)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Successfully exchanged authorization code for access token",
                    "zendeskSubdomain": zendesk_subdomain,
                    "secretName": secret_name,
                    "tokenExpiry": token_data.get("expires_at"),
                    "instructions": "The access token has been securely stored in AWS Secrets Manager. You can now create a Zendesk data source in Amazon Q Business.",
                }
            ),
        }
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Zendesk API Error", "message": str(e)})}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error", "message": str(e)})}


def parse_body(event):
    """Parse the API Gateway event body"""
    if "body-json" in event:
        return event["body-json"]

    if "body" in event:
        if isinstance(event["body"], str):
            return json.loads(event["body"])
        return event["body"]

    return {}


def get_state(state):
    """Retrieve state from DynamoDB"""
    table_name = os.environ.get("STATE_TABLE_NAME")
    if not table_name:
        raise ValueError("STATE_TABLE_NAME environment variable not set")

    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"id": state})

    if "Item" not in response:
        return None

    item = response["Item"]

    # Check if the state has expired
    if "expires" in item and item["expires"] < int(time.time()):
        # Delete the expired state
        table.delete_item(Key={"id": state})
        return None

    # Parse the data
    if "data" in item:
        return json.loads(item["data"])

    return None


def delete_state(state):
    """Delete state from DynamoDB"""
    table_name = os.environ.get("STATE_TABLE_NAME")
    if not table_name:
        return

    table = dynamodb.Table(table_name)

    table.delete_item(Key={"id": state})


def exchange_code_for_token(zendesk_subdomain, client_id, client_secret, code, redirect_uri):
    """Exchange authorization code for access token"""
    token_url = f"https://{zendesk_subdomain}.zendesk.com/oauth/tokens"

    # Prepare request data
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scope": "read write",
    }

    # Make request to token endpoint with timeout
    response = requests.post(token_url, data=data, timeout=30)
    response.raise_for_status()

    # Parse response
    token_data = response.json()

    # Add expiry timestamp if not present
    if "expires_in" in token_data and "expires_at" not in token_data:
        token_data["expires_at"] = int(time.time()) + token_data["expires_in"]

    return token_data


def store_token(secret_name, token_data, zendesk_subdomain):
    """Store token in AWS Secrets Manager"""
    try:
        # Create a simplified secret value with only the required fields
        secret_value = {
            "accessToken": token_data.get("access_token"),
            "hostUrl": f"https://{zendesk_subdomain}.zendesk.com/",
        }

        # Check if secret already exists
        try:
            secretsmanager.describe_secret(SecretId=secret_name)
            # Secret exists, update it
            secretsmanager.update_secret(SecretId=secret_name, SecretString=json.dumps(secret_value))
        except secretsmanager.exceptions.ResourceNotFoundException:
            # Secret doesn't exist, create it
            secretsmanager.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
                Description=f"Zendesk OAuth token for {zendesk_subdomain}",
            )

        return True
    except Exception as e:
        print(f"Error storing token in Secrets Manager: {str(e)}")
        raise


# For local testing
if __name__ == "__main__":
    os.environ["API_GATEWAY_URL"] = "https://example.com/"
    os.environ["STATE_TABLE_NAME"] = "zendesk-oauth-state"

    test_event = {"body-json": {"code": "test-auth-code", "state": "test-state"}}

    # Mock functions for local testing
    def mock_get_state(state):

        """Function mock_get_state."""

    
        """Function mock_get_state."""

        return {"clientId": "test-client-id", "clientSecret": "test-client-secret", "zendeskSubdomain": "example"}

    get_state = mock_get_state
    delete_state = lambda x: None

    # Comment out the actual API call for testing
    exchange_code_for_token = lambda a, b, c, d, e: {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "expires_in": 86400,
        "expires_at": int(time.time()) + 86400,
    }

    store_token = lambda a, b, c: True

    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
