# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os

import boto3
from botocore.exceptions import ClientError


def read_private_key(bucket, client_id, file_name="private.key"):
    """Function read_private_key."""

    """
    Read private key from S3 with server-side encryption
    
    Args:
        bucket (str): S3 bucket name
        client_id (str): Azure client ID used as subfolder
        file_name (str): File name within the client ID subfolder
        
    Returns:
        str: Private key content
    """
    s3_client = boto3.client("s3")

    # Construct the full path with client ID subfolder
    file_path = f"{client_id}/{file_name}"
    print(f"Reading private key from {bucket}/{file_path}")

    # Get the object with server-side encryption
    response = s3_client.get_object(Bucket=bucket, Key=file_path)

    # Read and decode the private key
    private_key_content = response["Body"].read().decode("utf-8")
    return private_key_content


def store_credentials_in_secrets_manager(
    secret_name,
    client_id,
    private_key,
    auth_type,
    description="API credentials",
    region_name="us-east-1",
):
    """Function store_credentials_in_secrets_manager."""

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    # Create the secret value as a JSON string
    secret_value = json.dumps({"clientId": client_id, "privateKey": private_key, "authType": auth_type})
    # Don't log sensitive information
    print("Preparing to store credentials in Secrets Manager")
    try:
        # Create the secret in AWS Secrets Manager
        response = client.create_secret(Name=secret_name, Description=description, SecretString=secret_value)
        print(f"Secret {secret_name} successfully created/updated")
        return response
    except ClientError as e:
        # Handle specific errors
        if e.response["Error"]["Code"] == "ResourceExistsException":
            # Secret already exists, update it
            response = client.update_secret(SecretId=secret_name, SecretString=secret_value)
            print(f"Secret {secret_name} already existed and was updated")
            return response
        else:
            # Handle other exceptions
            print(f"Error: {e}")
            raise


def create_data_source(application_id, index_id, configuration, data_source_name, role_arn):
    """Function create_data_source."""

    q = boto3.client("qbusiness")
    response = q.create_data_source(
        applicationId=application_id,
        indexId=index_id,
        displayName=data_source_name,
        configuration=configuration,
        syncSchedule="",
        roleArn=role_arn,
    )

    print(f"Data source creation response: {response}")
    return response


def config_for_sharepoint(secrets_arn, tenant_id, sharepoint_url, s3_bucket, client_id):
    """Function config_for_sharepoint."""

    # Use client ID subfolder for certificate path
    cert_file_name = f"{client_id}/sharepoint.crt"

    return {
        "connectionConfiguration": {
            "repositoryEndpointMetadata": {
                "domain": "awsplatodemo",
                "siteUrls": [
                    f"{sharepoint_url}",
                ],
                "repositoryAdditionalProperties": {
                    "version": "Online",
                    "onPremVersion": "",
                    "authType": "OAuth2Certificate",
                    "s3bucketName": f"{s3_bucket}",
                    "s3certificateName": f"{cert_file_name}",
                },
                "tenantId": f"{tenant_id}",
            }
        },
        "additionalProperties": {
            "crawlFiles": "true",
            "crawlPages": "true",
            "crawlEvents": "true",
            "crawlComments": "true",
            "crawlLinks": "true",
            "crawlAttachment": "true",
            "crawlListData": "true",
            "crawlAcl": "true",
            "isCrawlLocalGroupMapping": "true",
            "isCrawlAdGroupMapping": "false",
            "eventTitleFilterRegEx": [],
            "pageTitleFilterRegEx": [],
            "linkTitleFilterRegEx": [],
            "inclusionFilePath": [],
            "exclusionFilePath": [],
            "inclusionFileTypePatterns": [],
            "exclusionFileTypePatterns": [],
            "inclusionFileNamePatterns": [],
            "exclusionFileNamePatterns": [],
            "inclusionOneNoteSectionNamePatterns": [],
            "exclusionOneNoteSectionNamePatterns": [],
            "inclusionOneNotePageNamePatterns": [],
            "exclusionOneNotePageNamePatterns": [],
            "proxyPort": "",
            "fieldForUserId": "uuid",
            "includeSupportedFileType": "false",
            "maxFileSizeInMegaBytes": "5",
            "enableDeletionProtection": "false",
            "deletionProtectionThreshold": "0",
        },
        "enableIdentityCrawler": "true",
        "syncMode": "FORCED_FULL_CRAWL",
        "type": "SHAREPOINT",
        "secretArn": f"{secrets_arn}",
        "repositoryConfigurations": {
            "file": {
                "fieldMappings": [
                    {"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"},
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "lastModifiedDateTime",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUri"},
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "createdAt",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_authors", "indexFieldType": "STRING_LIST", "dataSourceFieldName": "author"},
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                ]
            },
            "event": {
                "fieldMappings": [
                    {"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"},
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "lastModifiedDateTime",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUri"},
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "createdDate",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                ]
            },
            "page": {
                "fieldMappings": [
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "createdDateTime",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "lastModifiedDateTime",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"},
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUri"},
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                ]
            },
            "link": {
                "fieldMappings": [
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "createdAt",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "lastModifiedDateTime",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_document_title", "indexFieldType": "STRING", "dataSourceFieldName": "title"},
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUri"},
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                ]
            },
            "attachment": {
                "fieldMappings": [
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "parentCreatedDate",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUri"},
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                ]
            },
            "comment": {
                "fieldMappings": [
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dataSourceFieldName": "createdDateTime",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    },
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "sourceUri"},
                    {"indexFieldName": "_authors", "indexFieldType": "STRING_LIST", "dataSourceFieldName": "author"},
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                ]
            },
        },
    }


def handler(event, context):
    """Function handler."""

    print(f"Received event: {event}")

    # Extract parameters from the request body
    application_id = event["body-json"]["applicationId"]
    index_id = event["body-json"]["indexId"]
    sharepoint_url = event["body-json"]["sharePointUrl"]
    tenant_id = event["body-json"]["tenantId"]
    client_id = event["body-json"]["clientId"]
    s3_bucket = event["body-json"]["s3Bucket"]
    data_source_name = event["body-json"]["dataSourceName"]

    # Read private key from S3 using client ID subfolder
    pk = read_private_key(s3_bucket, client_id)
    print("Private key retrieved successfully")

    # Extract domain from SharePoint URL
    from urllib.parse import urlparse

    parsed_url = urlparse(sharepoint_url)
    domain = parsed_url.netloc.split(".")[0]

    # Store credentials in Secrets Manager with domain and client_id
    secret_name = f"qbusiness-sharepoint-secret-{domain}-{client_id}"
    secret_response = store_credentials_in_secrets_manager(secret_name, client_id, pk, "OAuth2Certificate")

    # Create SharePoint configuration
    config = config_for_sharepoint(secret_response.get("ARN"), tenant_id, sharepoint_url, s3_bucket, client_id)

    # Create the data source
    response = create_data_source(
        application_id, index_id, config, data_source_name, os.environ["DATA_SOURCE_ROLE_ARN"]
    )

    data_source_id = response.get("dataSourceId")
    print(f"Data source created with ID: {data_source_id}")

    return {
        "statusCode": 200,
        "body": "QBusiness Data Source has been created",
        "response": {
            "dataSourceId": data_source_id,
            "applicationId": application_id,
            "indexId": index_id,
            "dataSourceName": data_source_name,
        },
    }


# For local testing only - will not run in Lambda
if __name__ == "__main__":
    os.environ["DATA_SOURCE_ROLE_ARN"] = "arn:aws:iam::123456789012:role/sharepoint-datasource-role"
    test_event = {
        "body-json": {
            "applicationId": "test-app-id",
            "indexId": "test-index-id",
            "sharePointUrl": "https://example.sharepoint.com/sites/test",
            "tenantId": "test-tenant-id",
            "clientId": "test-client-id",
            "s3Bucket": "test-bucket",
            "dataSourceName": "My SharePoint Data Source",
        }
    }
    handler(test_event, {})
