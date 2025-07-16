# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import time
import urllib.parse
import uuid

import boto3

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    """Function handler."""

    try:
        print(f"Received event: {event}")

        # Parse the request body
        body = parse_body(event)

        # Get required parameters
        client_id = body.get("clientId")
        client_secret = body.get("clientSecret")
        zendesk_subdomain = body.get("zendeskSubdomain")

        # Validate required parameters
        if not client_id or not client_secret or not zendesk_subdomain:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Missing Required Parameters",
                        "message": "Please provide clientId, clientSecret, and zendeskSubdomain",
                        "requiredParameters": ["clientId", "clientSecret", "zendeskSubdomain"],
                    }
                ),
            }

        # Get API Gateway URL for redirect URI
        api_gateway_url = os.environ.get("API_GATEWAY_URL", "")
        redirect_uri = f"{api_gateway_url}zendesk-oauth-callback"

        # Generate state for CSRF protection
        state = str(uuid.uuid4())

        # Store state in DynamoDB
        store_state(
            state, {"clientId": client_id, "clientSecret": client_secret, "zendeskSubdomain": zendesk_subdomain}
        )

        # Build authorization URL
        auth_url = build_auth_url(zendesk_subdomain, client_id, redirect_uri, state)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "authorizationUrl": auth_url,
                    "message": "Please visit this URL to authorize Amazon Q Business to access your Zendesk data",
                    "instructions": "After authorization, you will be redirected back to Amazon Q Business to complete the setup process.",
                }
            ),
        }
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


def build_auth_url(zendesk_subdomain, client_id, redirect_uri, state):
    """Build the Zendesk OAuth authorization URL"""
    base_url = f"https://{zendesk_subdomain}.zendesk.com/oauth/authorizations/new"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read write",
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"


def store_state(state, data, ttl_seconds=3600):
    """Store state in DynamoDB with TTL"""
    table_name = os.environ.get("STATE_TABLE_NAME")
    if not table_name:
        raise ValueError("STATE_TABLE_NAME environment variable not set")

    table = dynamodb.Table(table_name)

    # Calculate expiration time
    expires = int(time.time()) + ttl_seconds

    # Store the state
    table.put_item(Item={"id": state, "data": json.dumps(data), "expires": expires})

    return state


# For local testing
if __name__ == "__main__":
    os.environ["API_GATEWAY_URL"] = "https://example.com/"
    os.environ["STATE_TABLE_NAME"] = "zendesk-oauth-state"

    test_event = {
        "body-json": {"clientId": "test-client-id", "clientSecret": "test-client-secret", "zendeskSubdomain": "example"}
    }

    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
