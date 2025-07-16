# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os

import boto3

# Initialize AWS clients
qbusiness = boto3.client("qbusiness")
secretsmanager = boto3.client("secretsmanager")


def handler(event, context):
    """Function handler for creating Salesforce data source."""

    try:
        print(f"Received event: {event}")
        
        # Extract parameters from the event
        body = event.get("body-json", {})
        qbusiness_application_id = body.get("qBusinessApplicationId")
        qbusiness_index_id = body.get("qBusinessIndexId")
        data_source_name = body.get("dataSourceName")
        secret_name = body.get("secretName")
        
        # Optional configuration parameters
        sync_mode = body.get("syncMode", "FULL_CRAWL")
        include_knowledge_articles = body.get("includeKnowledgeArticles", True)
        include_chatter_feeds = body.get("includeChatterFeeds", False)
        include_cases = body.get("includeCases", True)
        include_opportunities = body.get("includeOpportunities", True)
        include_accounts = body.get("includeAccounts", True)
        include_contacts = body.get("includeContacts", True)
        crawl_attachments = body.get("crawlAttachments", True)
        
        # Validate required parameters
        if not all([qbusiness_application_id, qbusiness_index_id, data_source_name, secret_name]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Missing required parameters: qBusinessApplicationId, qBusinessIndexId, dataSourceName, secretName"
                })
            }
        
        # Retrieve and validate Salesforce credentials
        try:
            credentials = get_salesforce_credentials(secret_name)
        except Exception as e:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Secret Not Found",
                    "message": f"Failed to retrieve credentials: {str(e)}"
                })
            }
        
        # Create the Salesforce data source
        result = create_salesforce_data_source(
            qbusiness_application_id,
            qbusiness_index_id,
            data_source_name,
            credentials,
            secret_name,
            {
                "syncMode": sync_mode,
                "includeKnowledgeArticles": include_knowledge_articles,
                "includeChatterFeeds": include_chatter_feeds,
                "includeCases": include_cases,
                "includeOpportunities": include_opportunities,
                "includeAccounts": include_accounts,
                "includeContacts": include_contacts,
                "crawlAttachments": crawl_attachments
            }
        )
        
        if result["success"]:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Salesforce data source created successfully!",
                    "dataSourceId": result["dataSourceId"],
                    "dataSourceArn": result["dataSourceArn"],
                    "secretName": secret_name,
                    "syncJobId": result.get("syncJobId"),
                    "configuration": {
                        "hostUrl": credentials["hostUrl"],
                        "syncMode": sync_mode,
                        "includedObjects": get_included_objects_list({
                            "includeKnowledgeArticles": include_knowledge_articles,
                            "includeChatterFeeds": include_chatter_feeds,
                            "includeCases": include_cases,
                            "includeOpportunities": include_opportunities,
                            "includeAccounts": include_accounts,
                            "includeContacts": include_contacts
                        })
                    }
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Data Source Creation Failed",
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


def get_salesforce_credentials(secret_name):
    """Retrieve Salesforce credentials from AWS Secrets Manager."""
    
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        
        # Validate that all required fields are present
        required_fields = ['hostUrl', 'username', 'password', 'securityToken', 'consumerKey', 'consumerSecret']
        for field in required_fields:
            if field not in secret_data:
                raise ValueError(f"Missing required field in secret: {field}")
        
        return secret_data
        
    except Exception as e:
        print(f"Error retrieving credentials from Secrets Manager: {str(e)}")
        raise Exception(f"Failed to retrieve credentials: {str(e)}")


def create_salesforce_data_source(qbusiness_application_id, qbusiness_index_id, data_source_name, 
                                credentials, secret_name, config):
    """Create Salesforce data source in Amazon Q Business."""
    
    try:
        # Get the data source role ARN from environment variables
        data_source_role_arn = os.environ.get("DATA_SOURCE_ROLE_ARN")
        if not data_source_role_arn:
            raise Exception("DATA_SOURCE_ROLE_ARN environment variable not set")
        
        # Build the Salesforce configuration
        salesforce_config = build_salesforce_configuration(credentials, secret_name, config)
        
        print(f"Creating Salesforce data source with config: {json.dumps(salesforce_config)}")
        
        # Create the data source
        response = qbusiness.create_data_source(
            applicationId=qbusiness_application_id,
            indexId=qbusiness_index_id,
            displayName=data_source_name,
            configuration=salesforce_config,
            roleArn=data_source_role_arn,
            syncSchedule="",  # Empty string for on-demand sync (following ServiceNow pattern)
            description=f"Salesforce data source created via Amazon Q Business connector"
        )
        
        data_source_id = response.get("dataSourceId")
        data_source_arn = response.get("dataSourceArn")
        
        if not data_source_id:
            return {
                "success": False,
                "error": "Data source created but no ID returned",
                "details": str(response)
            }
        
        print(f"Successfully created data source: {data_source_id}")
        
        return {
            "success": True,
            "dataSourceId": data_source_id,
            "dataSourceArn": data_source_arn
        }
        
    except Exception as e:
        print(f"Error creating Salesforce data source: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": "Failed to create Salesforce data source in Q Business"
        }


def build_salesforce_configuration(credentials, secret_name, config):
    """Build the Salesforce configuration for Q Business data source."""
    
    # Get the full secret ARN
    secret_arn = get_secret_arn(secret_name)
    
    # Build repository configurations based on selected objects
    repository_configs = {}
    
    # Initialize additional properties with all boolean flags set to enable comprehensive crawling
    additional_properties = {
        # Enable all standard objects
        "isCrawlAccount": True,
        "isCrawlContact": True,
        "isCrawlCase": True,
        "isCrawlCampaign": True,
        "isCrawlProduct": True,
        "isCrawlLead": True,
        "isCrawlContract": True,
        "isCrawlPartner": True,
        "isCrawlProfile": True,
        "isCrawlIdea": True,
        "isCrawlPricebook": True,
        "isCrawlDocument": True,
        "isCrawlGroup": True,
        "isCrawlOpportunity": True,
        "isCrawlChatter": True,
        "isCrawlUser": True,
        "isCrawlSolution": True,
        "isCrawlTask": True,
        "crawlSharedDocument": True,
        "isCrawlAcl": True,  # Enable ACL crawling
        
        # Knowledge Articles with all statuses
        "isCrawlKnowledgeArticles": {
            "isCrawlDraft": True,
            "isCrawlPublish": True,
            "isCrawlArchived": True
        },
        
        # Enable attachments for ALL objects
        "isCrawlAccountAttachments": True,
        "isCrawlContactAttachments": True,
        "isCrawlCaseAttachments": True,
        "isCrawlCampaignAttachments": True,
        "isCrawlLeadAttachments": True,
        "isCrawlContractAttachments": True,
        "isCrawlGroupAttachments": True,
        "isCrawlOpportunityAttachments": True,
        "isCrawlChatterAttachments": True,
        "isCrawlSolutionAttachments": True,
        "isCrawlTaskAttachments": True,
        "isCrawlCustomEntityAttachments": True,
        
        # File type patterns - include all common file types
        "inclusionDocumentFileTypePatterns": [".*"],
        "inclusionAccountFileTypePatterns": [".*"],
        "inclusionCampaignFileTypePatterns": [".*"],
        "inclusionCaseFileTypePatterns": [".*"],
        "inclusionContactFileTypePatterns": [".*"],
        "inclusionContractFileTypePatterns": [".*"],
        "inclusionLeadFileTypePatterns": [".*"],
        "inclusionOpportunityFileTypePatterns": [".*"],
        "inclusionSolutionFileTypePatterns": [".*"],
        "inclusionTaskFileTypePatterns": [".*"],
        "inclusionGroupFileTypePatterns": [".*"],
        "inclusionChatterFileTypePatterns": [".*"],
        "inclusionCustomEntityFileTypePatterns": [".*"],
        
        # File name patterns - include all files
        "inclusionDocumentFileNamePatterns": [".*"],
        "inclusionAccountFileNamePatterns": [".*"],
        "inclusionCampaignFileNamePatterns": [".*"],
        "inclusionCaseFileNamePatterns": [".*"],
        "inclusionContactFileNamePatterns": [".*"],
        "inclusionContractFileNamePatterns": [".*"],
        "inclusionLeadFileNamePatterns": [".*"],
        "inclusionOpportunityFileNamePatterns": [".*"],
        "inclusionSolutionFileNamePatterns": [".*"],
        "inclusionTaskFileNamePatterns": [".*"],
        "inclusionGroupFileNamePatterns": [".*"],
        "inclusionChatterFileNamePatterns": [".*"],
        "inclusionCustomEntityFileNamePatterns": [".*"],
        
        # Set maximum file size to 50 MB
        "maxFileSizeInMegaBytes": "50"
    }
    
    # Knowledge Articles
    if config.get("includeKnowledgeArticles", True):
        repository_configs["knowledgeArticles"] = {
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Title",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Summary",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        }
        additional_properties["isCrawlKnowledgeArticles"] = {
            "isCrawlDraft": True,
            "isCrawlPublish": True,
            "isCrawlArchived": False
        }
    
    # Cases
    if config.get("includeCases", False):
        repository_configs["case"] = {
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Subject",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        }
        additional_properties["isCrawlCase"] = True
        if config.get("crawlAttachments", True):
            additional_properties["isCrawlCaseAttachments"] = True
    
    # Opportunities
    if config.get("includeOpportunities", False):
        repository_configs["opportunity"] = {
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Name",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        }
        additional_properties["isCrawlOpportunity"] = True
        if config.get("crawlAttachments", True):
            additional_properties["isCrawlOpportunityAttachments"] = True
    
    # Accounts
    if config.get("includeAccounts", False):
        repository_configs["account"] = {
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Name",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        }
        additional_properties["isCrawlAccount"] = True
        if config.get("crawlAttachments", True):
            additional_properties["isCrawlAccountAttachments"] = True
    
    # Contacts
    if config.get("includeContacts", False):
        repository_configs["contact"] = {
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Name",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        }
        additional_properties["isCrawlContact"] = True
        if config.get("crawlAttachments", True):
            additional_properties["isCrawlContactAttachments"] = True
    
    # Chatter
    if config.get("includeChatterFeeds", False):
        repository_configs["chatter"] = {
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Body",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        }
        additional_properties["isCrawlChatter"] = True
        if config.get("crawlAttachments", True):
            additional_properties["isCrawlChatterAttachments"] = True
    
    # Salesforce configuration following exact AWS Q Business schema
    salesforce_config = {
        "type": "SALESFORCE",
        "connectionConfiguration": {
            "repositoryEndpointMetadata": {
                "hostUrl": credentials["hostUrl"]
            }
        },
        "repositoryConfigurations": repository_configs,
        "additionalProperties": additional_properties,
        "secretArn": secret_arn,
        "syncMode": config.get("syncMode", "FULL_CRAWL")
    }
    
    return salesforce_config


def get_secret_arn(secret_name):
    """Get the full ARN of the secret."""
    try:
        response = secretsmanager.describe_secret(SecretId=secret_name)
        return response['ARN']
    except Exception as e:
        print(f"Warning: Could not get secret ARN, using constructed ARN: {str(e)}")
        # Fallback to constructed ARN
        return f"arn:aws:secretsmanager:{boto3.Session().region_name}:{boto3.client('sts').get_caller_identity()['Account']}:secret:{secret_name}"


def build_standard_object_configurations(config):
    """Build standard object configurations for Salesforce."""
    standard_objects = []
    
    if config.get("includeKnowledgeArticles", True):
        standard_objects.append({
            "name": "KnowledgeArticle",
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Title",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Summary",
                    "indexFieldName": "_document_body", 
                    "indexFieldType": "STRING"
                }
            ]
        })
    
    if config.get("includeCases", True):
        standard_objects.append({
            "name": "Case",
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Subject",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        })
    
    if config.get("includeOpportunities", True):
        standard_objects.append({
            "name": "Opportunity",
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Name",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        })
    
    if config.get("includeAccounts", True):
        standard_objects.append({
            "name": "Account",
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Name",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        })
    
    if config.get("includeContacts", True):
        standard_objects.append({
            "name": "Contact",
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Name",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Description",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        })
    
    if config.get("includeChatterFeeds", False):
        standard_objects.append({
            "name": "FeedItem",
            "fieldMappings": [
                {
                    "dataSourceFieldName": "Title",
                    "indexFieldName": "_document_title",
                    "indexFieldType": "STRING"
                },
                {
                    "dataSourceFieldName": "Body",
                    "indexFieldName": "_document_body",
                    "indexFieldType": "STRING"
                }
            ]
        })
    
    return standard_objects


def get_included_objects_list(config):
    """Get a list of included Salesforce objects for display purposes."""
    
    included_objects = []
    
    if config.get("includeKnowledgeArticles", True):
        included_objects.append("Knowledge Articles")
    if config.get("includeCases", True):
        included_objects.append("Cases")
    if config.get("includeOpportunities", True):
        included_objects.append("Opportunities")
    if config.get("includeAccounts", True):
        included_objects.append("Accounts")
    if config.get("includeContacts", True):
        included_objects.append("Contacts")
    if config.get("includeChatterFeeds", False):
        included_objects.append("Chatter Feeds")
    
    return included_objects
