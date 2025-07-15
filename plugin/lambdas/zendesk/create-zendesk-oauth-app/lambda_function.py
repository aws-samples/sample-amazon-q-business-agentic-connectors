# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import time

import requests


def handler(event, context):



    """Function handler."""




    """Function handler."""

    try:
        print(f"Received event: {event}")

        # Get API Gateway URL for redirect URI
        api_gateway_url = os.environ.get("API_GATEWAY_URL", "")
        redirect_uri = f"{api_gateway_url}zendesk-oauth-callback"

        return create_oauth_app(event, redirect_uri)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Zendesk API Error", "message": str(e)})}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error", "message": str(e)})}


def create_oauth_app(event, redirect_uri):



    """Function create_oauth_app."""




    """Function create_oauth_app."""

    """Create OAuth app automatically using Zendesk API"""
    body = event["body-json"]
    zendesk_subdomain = body.get("zendeskSubdomain")
    admin_email = body.get("adminEmail")
    api_token = body.get("apiToken")
    app_name = body.get("appName")

    api_url = f"https://{zendesk_subdomain}.zendesk.com/api/v2/oauth/clients.json"
    payload = {
        "client": {
            "name": app_name,
            "identifier": f"amazon-q-business-{int(time.time())}",
            "redirect_uri": redirect_uri,
            "description": "Connector for integrating Zendesk with Amazon Q Business",
            "scopes": ["read", "write"],
            "kind": "confidential",
        }
    }

    print(f"Creating OAuth client with payload: {json.dumps(payload)}")

    response = requests.post(
        api_url,
        json=payload,
        auth=(f"{admin_email}/token", api_token),
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    response.raise_for_status()
    response_data = response.json()

    # Log only non-sensitive information
    print(f"Zendesk API response received. Status: success, Client ID: {response_data['client']['identifier']}")

    client_id = response_data["client"]["identifier"]
    client_secret = response_data["client"]["secret"]

    response_obj = {
        "app_name": app_name,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "zendesk_subdomain": zendesk_subdomain,
    }

    return {
        "statusCode": 200,
        "body": f"Zendesk OAuth application created successfully! App Name: {app_name}, Client ID: {client_id}, Client Secret: {client_secret}, Redirect URI: {redirect_uri}",
        "response": response_obj,
    }


# For local testing
if __name__ == "__main__":
    os.environ["API_GATEWAY_URL"] = "https://example.com/"
    test_event = {
        "body-json": {
            "zendeskSubdomain": "example",
            "adminEmail": "admin@example.com",
            "apiToken": "test_token",
            "appName": "Test Q Business Connector",
        }
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
