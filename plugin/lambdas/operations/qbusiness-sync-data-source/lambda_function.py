# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from datetime import datetime

import boto3


def handler(event, context):



    """Function handler."""




    """Function handler."""

    application_id = None
    index_id = None
    datasource_id = None
    qb_client = boto3.client("qbusiness")

    try:
        print(f"Received event: {json.dumps(event)}")

        # Extract parameters from the body-json structure with fallbacks for different parameter names
        body = event.get("body-json", {})

        # Handle different parameter naming conventions
        application_id = body.get("qbusinessApplicationId") or body.get("applicationId")
        index_id = body.get("qindexId") or body.get("indexId")
        datasource_id = body.get("qdatasourceId") or body.get("datasourceId") or body.get("dataSourceId")

        print(f"Extracted parameters: applicationId={application_id}, indexId={index_id}, datasourceId={datasource_id}")

        if not all([application_id, index_id, datasource_id]):
            error_msg = "Missing required parameters. Please provide applicationId, indexId, and datasourceId"
            print(error_msg)
            raise ValueError(error_msg)

        sync_params = {"applicationId": application_id, "indexId": index_id, "dataSourceId": datasource_id}

        print(f"Starting sync job with parameters: {json.dumps(sync_params)}")
        response = qb_client.start_data_source_sync_job(**sync_params)
        print(f"Sync job started successfully: {json.dumps(response)}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Data source sync job started successfully",
                    "executionId": response.get("executionId"),
                    "applicationId": application_id,
                    "indexId": index_id,
                    "datasourceId": datasource_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        }

    except qb_client.exceptions.ConflictException as ce:
        print("A sync is already in progress for this data source")
        return {
            "statusCode": 409,
            "body": json.dumps(
                {
                    "message": "A sync is already in progress for this data source",
                    "applicationId": application_id,
                    "indexId": index_id,
                    "datasourceId": datasource_id,
                }
            ),
        }

    except Exception as e:
        print(f"Lambda execution failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": f"Error: {str(e)}",
                    "applicationId": application_id,
                    "indexId": index_id,
                    "datasourceId": datasource_id,
                }
            ),
        }
