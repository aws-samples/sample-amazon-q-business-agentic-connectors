# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from datetime import datetime, timedelta

import boto3


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):

        """Function default."""

    
        """Function default."""

        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def handler(event, context):



    """Function handler."""




    """Function handler."""

    print(f"Received event: {json.dumps(event)}")
    q_client = boto3.client("qbusiness")
    since = event.get("since", "5")

    try:
        # Extract parameters from the body-json structure with fallbacks for different parameter names
        body = event.get("body-json", {})

        # Handle different parameter naming conventions
        application_id = body.get("qbusinessApplicationId") or body.get("applicationId")
        index_id = body.get("qindexId") or body.get("indexId")
        data_source_id = body.get("qdatasourceId") or body.get("datasourceId") or body.get("dataSourceId")

        print(
            f"Extracted parameters: applicationId={application_id}, indexId={index_id}, datasourceId={data_source_id}"
        )

        if not all([application_id, index_id, data_source_id]):
            error_msg = "Missing required parameters. Please provide applicationId, indexId, and datasourceId"
            print(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing Required Parameters", "message": error_msg}),
            }

        end_time = datetime.now() + timedelta(days=1)
        start_time = datetime.now() - timedelta(hours=int(since))

        print(
            f"Fetching sync summary for Application ID: {application_id}, datasource ID: {data_source_id}, index ID: {index_id} from {start_time} to {end_time}"
        )

        response = q_client.list_data_source_sync_jobs(
            dataSourceId=data_source_id,
            applicationId=application_id,
            maxResults=10,
            indexId=index_id,
            startTime=start_time,
            endTime=end_time,
        )

        json_data = json.dumps(response, cls=DateTimeEncoder)
        print(f"Response: {json_data}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Sync history fetched successfully", "metrics": json.loads(json_data)["history"]},
                cls=DateTimeEncoder,
            ),
        }

    except KeyError as ke:
        print(f"Missing required parameter: {str(ke)}")
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "Missing Required Parameter", "message": f"Missing required parameter: {str(ke)}"}
            ),
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error", "message": f"Error: {str(e)}"}),
        }
