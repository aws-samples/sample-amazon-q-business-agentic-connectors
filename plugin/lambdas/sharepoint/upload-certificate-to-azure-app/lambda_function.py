# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import base64
import json
import os
from datetime import datetime, timedelta

import boto3
import msal
import requests


def handler(event, context):
    """Function handler."""

    try:
        print(f"Received event: {event}")

        # Get configuration from event and environment variables
        s3_bucket = event["body-json"]["s3Bucket"]
        azure_tenant_id = event["body-json"]["tenantId"]
        azure_object_id = event["body-json"]["objectId"]
        azure_client_id = event["body-json"]["appId"]
        azure_client_secret = event["body-json"]["appSecret"]
        cert_display_name = "cert_display_name"

        # Use client ID subfolder for certificate path
        client_folder = f"{azure_client_id}/"
        s3_cert_key = f"{client_folder}sharepoint.crt"

        # Get certificate from S3
        cert_data = get_certificate_from_s3(s3_bucket, s3_cert_key)
        print(f"Certificate retrieved from S3: {s3_bucket}/{s3_cert_key}")

        # Get access token
        access_token = get_access_token(azure_tenant_id, azure_client_id, azure_client_secret)
        print("Access token acquired successfully")

        # Update application with certificate
        success = update_application_with_certificate(access_token, azure_object_id, cert_data, cert_display_name)
        print(f"Certificate uploaded to Azure application: {azure_object_id}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Certificate updated successfully",
                    "applicationId": azure_client_id,
                    "certificateName": cert_display_name or f"Certificate-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "certificatePath": s3_cert_key,
                }
            ),
        }

    except Exception as e:
        error_message = str(e)
        if hasattr(e, "response") and "body" in e.response:
            error_message = e.response["body"]

        print(f"Certificate update process failed: {error_message}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Certificate update process failed", "error": error_message}),
        }


def get_certificate_from_s3(bucket_name, cert_key):
    """Function get_certificate_from_s3."""

    """
    Download the certificate file from S3 bucket
    """
    try:
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket_name, Key=cert_key)
        cert_data = response["Body"].read()
        print(f"Successfully retrieved certificate from S3: {bucket_name}/{cert_key}")
        return cert_data
    except Exception as e:
        print(f"Error retrieving certificate from S3: {str(e)}")
        raise


def get_access_token(tenant_id, client_id, client_secret):
    """Function get_access_token."""

    """
    Get Microsoft Graph API access token using client credentials flow
    """
    try:
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id=client_id, client_credential=client_secret, authority=authority
        )

        # The scope needed for application management
        scopes = ["https://graph.microsoft.com/.default"]

        result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            print("Successfully acquired access token")
            return result["access_token"]
        else:
            print(f"Error acquiring token: {result.get('error_description', 'Unknown error')}")
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
    except Exception as e:
        print(f"Error in authentication: {str(e)}")
        raise


def update_application_with_certificate(access_token, application_id, cert_data, cert_display_name=None):
    """Function update_application_with_certificate."""

    """
    Update an Azure application with a new certificate
    """
    try:
        # Base64 encode the certificate data
        cert_base64 = base64.b64encode(cert_data).decode("utf-8")

        # Calculate expiry date (certificates typically have this info embedded,
        # but for this example we'll set it to 1 year from now)
        start_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date = "2026-04-10"

        # Prepare the certificate data for the Graph API
        display_name = cert_display_name or f"Certificate-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Prepare the request body
        key_credential = {
            "keyCredentials": [
                {
                    "type": "AsymmetricX509Cert",
                    "usage": "Verify",
                    "key": cert_base64,
                    "displayName": display_name,
                    "startDateTime": start_date,
                    "endDateTime": end_date,
                }
            ]
        }

        # Update the application
        graph_url = f"https://graph.microsoft.com/v1.0/applications/{application_id}"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        try:
            response = requests.patch(graph_url, headers=headers, data=json.dumps(key_credential), timeout=30)
            response.raise_for_status()
            print(f"Successfully updated application {application_id} with new certificate")
            return True
        except requests.exceptions.RequestException as e:
            error_details = (
                e.response.json()
                if hasattr(e, "response") and e.response and e.response.text
                else {"error": "No details available"}
            )
            print(f"Error updating application: {str(e)} - {error_details}")
            raise Exception(f"Failed to update application: {str(e)} - {error_details}")
    except Exception as e:
        print(f"Error updating application with certificate: {str(e)}")
        raise


# For local testing only - will not run in Lambda
if __name__ == "__main__":
    # Test event for local development
    test_event = {
        "body-json": {
            "s3Bucket": "your-s3-bucket-name",
            "tenantId": "your-tenant-id",
            "objectId": "application-id-to-update",
            "appId": "your-client-id",
            "appSecret": "your-client-secret",
        }
    }

    # Call the handler
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
