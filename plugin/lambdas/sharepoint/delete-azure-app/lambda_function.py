# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient


def handler(event, context):



    """Function handler."""




    """Function handler."""

    print(f"Received event: {event}")

    # Get parameters from event
    tenant_id = event["body-json"]["tenantId"]
    client_id = event["body-json"]["adminAppId"]
    client_secret = event["body-json"]["adminAppSecret"]  # Fixed parameter name
    app_id_to_delete = event["body-json"]["objectId"]

    # Validate required parameters
    if not all([tenant_id, client_id, client_secret, app_id_to_delete]):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "message": "Missing required parameters. Please provide tenantId, adminAppId, adminAppSecret, and objectId."
                }
            ),
        }

    try:
        # Create a credential object
        credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

        # Create a Graph client
        graph_client = GraphClient(credential=credential)

        # Delete the application
        response = graph_client.delete(f"/applications/{app_id_to_delete}")
        print(f"Successfully deleted application with ID: {app_id_to_delete}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Application with ID {app_id_to_delete} has been successfully deleted."}),
        }

    except Exception as e:
        print(f"Error deleting application: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"message": f"Error deleting application: {str(e)}"})}
