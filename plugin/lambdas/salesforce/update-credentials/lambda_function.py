# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

import boto3

# Initialize AWS clients
secretsmanager = boto3.client("secretsmanager")


def handler(event, context):
    """Function handler for updating Salesforce credentials with Consumer Key and Secret."""

    try:
        print(f"Received event: {event}")
        
        # Extract parameters from the event
        body = event.get("body-json", {})
        secret_name = body.get("secretName")
        consumer_key = body.get("consumerKey")
        consumer_secret = body.get("consumerSecret")
        
        # Validate required parameters
        if not all([secret_name, consumer_key, consumer_secret]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Missing required parameters: secretName, consumerKey, consumerSecret"
                })
            }
        
        # Update the existing secret with Consumer Key and Secret
        result = update_salesforce_credentials(secret_name, consumer_key, consumer_secret)
        
        if result["success"]:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Salesforce credentials updated successfully!",
                    "secretName": secret_name,
                    "consumerKey": consumer_key,
                    "consumerSecret": f"{consumer_secret[:4]}...{consumer_secret[-4:]}",  # Masked for security
                    "instructions": [
                        "Consumer Key and Consumer Secret have been stored successfully",
                        f"Secret name: {secret_name}",
                        f"Consumer Key: {consumer_key}",
                        "Consumer Secret: [STORED SECURELY]",
                        "Credentials are now ready for use",
                        "You can now proceed to test authentication",
                        "Use this secret name for creating the data source"
                    ]
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Credential Update Failed",
                    "message": result["error"],
                    "details": result.get("details", "")
                })
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal Server Error",
                "message": str(e)
            })
        }


def update_salesforce_credentials(secret_name, consumer_key, consumer_secret):
    """Update existing Salesforce credentials with Consumer Key and Secret."""
    
    try:
        # First, retrieve the existing secret
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        existing_credentials = json.loads(response['SecretString'])
        
        # Update the credentials with Consumer Key and Secret
        existing_credentials.update({
            "consumerKey": consumer_key,
            "consumerSecret": consumer_secret
        })
        
        # Update the secret in AWS Secrets Manager
        secretsmanager.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(existing_credentials),
            Description="Salesforce credentials for Amazon Q Business connector"
        )
        
        print(f"Successfully updated credentials in secret: {secret_name}")
        return {
            "success": True,
            "secretName": secret_name
        }
        
    except secretsmanager.exceptions.ResourceNotFoundException:
        return {
            "success": False,
            "error": "Secret not found",
            "details": f"The secret '{secret_name}' does not exist. Please create the Connected App first."
        }
    except Exception as e:
        print(f"Error updating credentials in Secrets Manager: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": "Failed to update credentials in Secrets Manager"
        }
