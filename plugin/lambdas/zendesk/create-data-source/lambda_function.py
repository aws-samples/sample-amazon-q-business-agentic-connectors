# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os

import boto3

# Initialize AWS clients
secretsmanager = boto3.client("secretsmanager")
qbusiness = boto3.client("qbusiness")


def handler(event, context):
    """Function handler."""

    try:
        print(f"Received event: {json.dumps(event)}")

        # Parse the request body
        body = parse_body(event)
        print(f"Parsed body: {json.dumps(body)}")

        # Get required parameters
        application_id = body.get("qbusinessApplicationId") or body.get("applicationId")
        index_id = body.get("qindexId") or body.get("indexId")
        data_source_name = body.get("dataSourceName")
        zendesk_subdomain = body.get("zendeskSubdomain")
        data_source_type = body.get("dataSourceType", "BOTH")  # Default to BOTH
        client_id = body.get("clientId")

        print(
            f"Parameters: applicationId={application_id}, indexId={index_id}, dataSourceName={data_source_name}, zendeskSubdomain={zendesk_subdomain}, dataSourceType={data_source_type}, clientId={client_id}"
        )

        # Validate required parameters
        if not application_id or not index_id or not zendesk_subdomain:
            print("Missing required parameters")
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Bad Request",
                        "message": "Missing required parameters: qbusinessApplicationId, qindexId, zendeskSubdomain",
                    }
                ),
            }

        if not data_source_name:
            data_source_name = f"Zendesk-{zendesk_subdomain}"
            print(f"Using default data source name: {data_source_name}")

        # Find the secret ARN for the Zendesk OAuth token
        secret_arn = find_secret_arn_by_subdomain(zendesk_subdomain, client_id)

        if not secret_arn:
            print(f"No OAuth token found for {zendesk_subdomain}")
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Bad Request",
                        "message": "No OAuth token found for the provided Zendesk subdomain. Please complete the OAuth flow first.",
                    }
                ),
            }

        # Get the IAM role ARN for the data source
        data_source_role_arn = os.environ.get("DATA_SOURCE_ROLE_ARN")
        print(f"Data source role ARN: {data_source_role_arn}")

        if not data_source_role_arn:
            print("DATA_SOURCE_ROLE_ARN environment variable not set")
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"error": "Internal Server Error", "message": "Data source role ARN not configured"}
                ),
            }

        # Create the data source
        config = {
            "qbusinessApplicationId": application_id,
            "qindexId": index_id,
            "zendeskSubdomain": zendesk_subdomain,
            "secretArn": secret_arn,
            "dataSourceName": data_source_name,
            "dataSourceType": data_source_type,
        }

        create_result = create_data_source(config, data_source_role_arn)
        print(f"CreateDataSource API Response: {json.dumps(create_result)}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully created Zendesk data source '{data_source_name}' for subdomain '{zendesk_subdomain}'. The data source is now being created with ID: {create_result['dataSourceId']}.",
                    "instructions": "The next step is to initiate the first synchronization of your Zendesk data with Amazon Q Business. This will import your Zendesk content into the Q index. Would you like me to start the synchronization process now?",
                    "dataSourceId": create_result["dataSourceId"],
                    "applicationId": application_id,
                    "indexId": index_id,
                    "status": "CREATING",
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
            try:
                return json.loads(event["body"])
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON body: {str(e)}")
                return {}
        return event["body"]

    return {}


def find_secret_arn_by_subdomain(zendesk_subdomain, client_id):
    """Function find_secret_arn_by_subdomain and client ID"""
    unique_id = client_id.split("-")[-1]
    secret_name = f"qbusiness-zendesk-secret-{zendesk_subdomain}-{unique_id}"

    try:
        # First try with the exact name
        try:
            response = secretsmanager.describe_secret(SecretId=secret_name)
            print(f"Found secret ARN for subdomain {zendesk_subdomain}: {response['ARN']}")
            return response["ARN"]
        except secretsmanager.exceptions.ResourceNotFoundException:
            print(f"Secret {secret_name} not found, trying to list secrets")

        # If not found, list secrets with the name filter
        response = secretsmanager.list_secrets(Filters=[{"Key": "name", "Values": [f"zendesk-oauth-token"]}])

        # Find the matching secret
        for secret in response.get("SecretList", []):
            if zendesk_subdomain in secret["Name"]:
                print(f"Found matching secret: {secret['Name']} with ARN: {secret['ARN']}")
                return secret["ARN"]

        print(f"No secret found for subdomain {zendesk_subdomain}")
        return None
    except Exception as e:
        print(f"Error finding secret ARN: {str(e)}")
        return None


def generate_zendesk_configuration(secret_arn, zendesk_subdomain, data_source_type):
    """Generate the configuration for a Zendesk data source"""
    # Determine which content types to crawl based on dataSourceType
    crawl_article = data_source_type == "GUIDE" or data_source_type == "BOTH"
    crawl_ticket = data_source_type == "SUPPORT" or data_source_type == "BOTH"

    return {
        "connectionConfiguration": {
            "repositoryEndpointMetadata": {
                "hostUrl": f"https://{zendesk_subdomain}.zendesk.com/",
                "authType": "Oauth2-ImplicitGrantFlow",
            }
        },
        "additionalProperties": {
            # Organization filters
            "organizationNameFilter": [],
            # Date filters
            "sinceDate": None,
            # Content type flags
            "isCrawTicket": str(crawl_ticket).lower(),
            "isCrawTicketComment": str(crawl_ticket).lower(),
            "isCrawTicketCommentAttachment": "false",
            "isCrawlArticle": str(crawl_article).lower(),
            "isCrawlArticleAttachment": "false",
            "isCrawlArticleComment": "false",
            "isCrawlCommunityTopic": "false",
            "isCrawlCommunityPost": "false",
            "isCrawlCommunityPostComment": "false",
            # Access control - Enable ACL for security
            "isCrawlAcl": True,
            "fieldForUserId": "uuid",
            # Content filters
            "inclusionPatterns": [],
            "exclusionPatterns": [],
            # File handling
            "maxFileSizeInMegaBytes": "50",
            "includeSupportedFileType": False,
            # Deletion protection
            "enableDeletionProtection": False,
            "deletionProtectionThreshold": "0",
        },
        "enableIdentityCrawler": True,
        "syncMode": "FORCED_FULL_CRAWL",
        "type": "ZENDESK",
        "secretArn": secret_arn,
        "repositoryConfigurations": generate_repository_configurations(),
    }


def generate_repository_configurations():
    """Generate repository configurations with field mappings for different content types"""
    # Common field mappings that apply to multiple content types
    common_field_mappings = [
        {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
        {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUrl"},
        {
            "indexFieldName": "_created_at",
            "indexFieldType": "DATE",
            "dataSourceFieldName": "createdAt",
            "dateFieldFormat": "dd-MM-yyyy HH:mm:ss",
        },
        {
            "indexFieldName": "_last_updated_at",
            "indexFieldType": "DATE",
            "dataSourceFieldName": "updatedAt",
            "dateFieldFormat": "dd-MM-yyyy HH:mm:ss",
        },
    ]

    # Author field mapping - only used in some content types
    author_field_mapping = {
        "indexFieldName": "_authors",
        "indexFieldType": "STRING_LIST",
        "dataSourceFieldName": "authors",
    }

    # Create configurations for each content type
    return {
        # Ticket configuration
        "ticket": {"fieldMappings": common_field_mappings + [author_field_mapping]},
        # Ticket comment configuration
        "ticketComment": {"fieldMappings": common_field_mappings + [author_field_mapping]},
        # Article configuration (for Zendesk Guide)
        "article": {
            "fieldMappings": common_field_mappings
            + [author_field_mapping]
            + [{"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"}]
        },
    }


def create_data_source(config, data_source_role_arn):
    """Create a data source in Amazon Q Business"""

    # Generate the Zendesk configuration
    data_source_configuration = generate_zendesk_configuration(
        config["secretArn"], config["zendeskSubdomain"], config["dataSourceType"]
    )

    # Create the data source parameters - follow the ServiceNow implementation
    create_params = {
        "applicationId": config["qbusinessApplicationId"],
        "indexId": config["qindexId"],
        "displayName": config["dataSourceName"],
        "configuration": data_source_configuration,
        "syncSchedule": "",
        "roleArn": data_source_role_arn,
        "description": f"Zendesk data source for {config['zendeskSubdomain']}",
    }

    # Log the configuration for debugging
    log_config = {
        "applicationId": config["qbusinessApplicationId"],
        "indexId": config["qindexId"],
        "displayName": config["dataSourceName"],
        "zendeskSubdomain": config["zendeskSubdomain"],
    }
    print(f"Creating Zendesk data source with configuration: {json.dumps(log_config)}")

    # Create the data source
    response = qbusiness.create_data_source(**create_params)
    return response


# For local testing
if __name__ == "__main__":
    os.environ["DATA_SOURCE_ROLE_ARN"] = "arn:aws:iam::123456789012:role/zendesk-datasource-role"

    test_event = {
        "body-json": {
            "qbusinessApplicationId": "test-app-id",
            "qindexId": "test-index-id",
            "dataSourceName": "Zendesk Guide Articles",
            "zendeskSubdomain": "example",
            "dataSourceType": "BOTH",
        }
    }

    # Mock functions for local testing
    find_secret_arn_by_subdomain = (
        lambda x: "arn:aws:secretsmanager:us-east-1:123456789012:secret:zendesk-oauth-token-example-1"
    )
    create_data_source = lambda a, b: {"id": "test-data-source-id"}

    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
