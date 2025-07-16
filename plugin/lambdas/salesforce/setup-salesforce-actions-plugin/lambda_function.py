# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import uuid

import boto3

# Initialize AWS clients
secretsmanager = boto3.client("secretsmanager")
qbusiness = boto3.client("qbusiness")
sts = boto3.client("sts")


def handler(event, context):
    """Function handler for setting up Salesforce Actions Plugin programmatically."""

    try:
        print(f"Received event: {event}")
        
        # Extract parameters from the event
        body = event.get("body-json", {})
        client_id = body.get("clientId")  # Consumer Key from Salesforce
        client_secret = body.get("clientSecret")  # Consumer Secret from Salesforce
        redirect_url = body.get("redirectUrl")  # Q Business endpoint + /oauth/callback
        salesforce_domain_url = body.get("salesforceDomainUrl")  # e.g., https://yourInstance.my.salesforce.com
        q_business_application_id = body.get("qBusinessApplicationId")
        plugin_name = body.get("pluginName", "Salesforce-Actions-Plugin")
        
        # Validate required parameters
        if not all([client_id, client_secret, redirect_url, salesforce_domain_url, q_business_application_id]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Missing required parameters: clientId, clientSecret, redirectUrl, salesforceDomainUrl, qBusinessApplicationId"
                })
            }
        
        # Ensure the Salesforce domain URL has the required API path
        salesforce_domain_url = salesforce_domain_url.rstrip('/')
        if not salesforce_domain_url.endswith('/services/data/v60.0'):
            salesforce_domain_url = f"{salesforce_domain_url}/services/data/v60.0"
        
        # Store Salesforce Actions credentials in AWS Secrets Manager
        secret_name = store_salesforce_actions_credentials(
            client_id, client_secret, redirect_url
        )
        
        # Create the Salesforce Actions Plugin in Q Business
        plugin_result = create_salesforce_actions_plugin(
            q_business_application_id, plugin_name, salesforce_domain_url, secret_name
        )
        
        if plugin_result["success"]:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Salesforce Actions Plugin created successfully!",
                    "pluginId": plugin_result["pluginId"],
                    "pluginArn": plugin_result["pluginArn"],
                    "secretName": secret_name,
                    "qBusinessApplicationId": q_business_application_id,
                    "configuration": {
                        "pluginName": plugin_name,
                        "salesforceDomainUrl": salesforce_domain_url,
                        "clientId": client_id,
                        "redirectUrl": redirect_url,
                        "accessTokenUrl": "https://login.salesforce.com/services/oauth2/token",
                        "authorizationUrl": "https://login.salesforce.com/services/oauth2/authorize"
                    },
                    "instructions": [
                        "Salesforce Actions Plugin has been created successfully!",
                        f"Plugin ID: {plugin_result['pluginId']}",
                        f"Plugin Name: {plugin_name}",
                        f"Secret Name: {secret_name}",
                        "Users can now perform Salesforce actions from Amazon Q Business",
                        "Available actions include:",
                        "- Create/Update/View Salesforce records",
                        "- Search Salesforce data",
                        "- Execute Salesforce workflows",
                        "Actions depend on user permissions in Salesforce"
                    ]
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Salesforce Actions Plugin Creation Failed",
                    "message": plugin_result["error"],
                    "details": plugin_result.get("details", ""),
                    "secretName": secret_name  # Still return secret name even if plugin creation fails
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


def store_salesforce_actions_credentials(client_id, client_secret, redirect_url):
    """Store Salesforce Actions credentials in AWS Secrets Manager."""
    
    # Generate a unique secret name for Actions
    secret_name = f"QBusiness-Salesforce_crm-plugin-{str(uuid.uuid4())[:8]}"
    
    # Prepare the secret value with the exact format expected by Q Business
    secret_value = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_url
    }
    
    try:
        # Create the secret in AWS Secrets Manager
        secretsmanager.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret_value),
            Description="Salesforce Actions credentials for Amazon Q Business Actions Plugin"
        )
        
        print(f"Successfully stored Salesforce Actions credentials in secret: {secret_name}")
        return secret_name
        
    except Exception as e:
        print(f"Error storing Actions credentials in Secrets Manager: {str(e)}")
        raise Exception(f"Failed to store Actions credentials: {str(e)}")


def create_salesforce_actions_plugin(q_business_application_id, plugin_name, salesforce_domain_url, secret_name):
    """Create the Salesforce Actions Plugin in Amazon Q Business using the correct CreatePlugin API structure."""
    
    try:
        # Get the full secret ARN
        secret_arn = get_secret_arn(secret_name)
        
        # Get the pre-created plugin service role ARN from environment variable
        plugin_role_arn = os.environ.get('PLUGIN_SERVICE_ROLE_ARN')
        if not plugin_role_arn:
            raise Exception("PLUGIN_SERVICE_ROLE_ARN environment variable not set")
        
        print(f"Creating Salesforce Actions plugin with essential parameters only")
        
        # Create the plugin using the correct CreatePlugin API structure
        response = qbusiness.create_plugin(
            applicationId=q_business_application_id,
            displayName=plugin_name,
            type="SALESFORCE_CRM",
            authConfiguration={
                "oAuth2ClientCredentialConfiguration": {
                    "secretArn": secret_arn,
                    "roleArn": plugin_role_arn,
                    "authorizationUrl": "https://login.salesforce.com/services/oauth2/authorize",
                    "tokenUrl": "https://login.salesforce.com/services/oauth2/token"
                }
            },
            serverUrl=salesforce_domain_url
        )
        
        plugin_id = response.get("pluginId")
        plugin_arn = response.get("pluginArn")
        
        print(f"Successfully created Salesforce Actions plugin: {plugin_id}")
        
        return {
            "success": True,
            "pluginId": plugin_id,
            "pluginArn": plugin_arn
        }
        
    except Exception as e:
        print(f"Error creating Salesforce Actions plugin: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": "Failed to create Salesforce Actions plugin in Q Business using CreatePlugin API"
        }


def get_secret_arn(secret_name):
    """Get the full ARN of the secret."""
    try:
        response = secretsmanager.describe_secret(SecretId=secret_name)
        return response['ARN']
    except Exception as e:
        print(f"Warning: Could not get secret ARN, using constructed ARN: {str(e)}")
        # Fallback to constructed ARN
        account_id = sts.get_caller_identity()['Account']
        region = boto3.Session().region_name
        return f"arn:aws:secretsmanager:{region}:{account_id}:secret:{secret_name}"
