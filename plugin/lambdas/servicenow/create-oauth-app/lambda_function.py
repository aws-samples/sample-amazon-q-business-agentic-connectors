# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import uuid

import requests
from pysnc import ServiceNowClient


def handler(event, context):



    """Function handler."""




    """Function handler."""

    try:
        print(f"received event: {event}")
        return insert(event)
    except requests.exceptions.RequestException as e:
        print(e)
        return {"statusCode": 500, "body": json.dumps({"error": "ServiceNow API Error", "message": str(e)})}
    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error", "message": str(e)})}


def insert(event):



    """Function insert."""




    """Function insert."""

    appname = event["body-json"]["name"]
    username = event["body-json"]["username"]
    password = event["body-json"]["password"]
    instance = event["body-json"]["instance"]
    redirect_url = event["body-json"]["redirectUrl"]

    client = ServiceNowClient(f"https://{instance}.service-now.com", (username, password))
    gr = client.GlideRecord("oauth_entity")
    gr.initialize()

    client_secret = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    app_name = f"{appname}-{str(uuid.uuid4())}"
    gr.name = app_name
    gr.client_id = client_id
    gr.client_secret = client_secret
    gr.redirect_url = redirect_url
    gr.logo_url = "https://your-logo-url.com/logo.png"
    gr.access_token_lifespan = 3600
    gr.refresh_token_lifespan = 8640000
    gr.grant_types = "authorization_code,refresh_token"
    sysID = gr.insert()

    response = {"app_name": app_name, "client_id": gr.client_id, "client_secret": client_secret, "sys_id": sysID}
    print(f"Response: {response}")

    return {"statusCode": 200, "body": "ServiceNow OAuth App is successfully created", "response": response}


# For local testing only - will not run in Lambda
if __name__ == "__main__":
    # Test event for local development
    test_event = {
        "body-json": {
            "name": "connector-q-snow123",
            "password": "123456abcd",
            "instance": "dev00001",
            "redirectUrl": "https://123355.chat.qbusiness.us-east-1.on.aws/oauth/callback",
            "username": "admin",
        }
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
