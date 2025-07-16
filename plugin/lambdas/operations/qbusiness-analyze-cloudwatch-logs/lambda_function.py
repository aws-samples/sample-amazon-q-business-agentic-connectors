# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from datetime import datetime, timedelta

import boto3


def get_field_value(json_structure, field_name):
    """
    Extract a field value from a JSON structure.
    
    Args:
        json_structure: The JSON structure to extract from
        field_name: The name of the field to extract
        
    Returns:
        The value of the field, or None if not found
    """
    try:
        return next((item["value"] for item in json_structure if item["field"] == field_name), None)
    except Exception as e:
        print(f"Error extracting field value: {str(e)}")
        return None


def handler(event, context):
    """
    Lambda handler function to analyze CloudWatch logs.
    
    Args:
        event: The event dict that contains the parameters passed
        context: The context in which the function is called
        
    Returns:
        The response dict containing status code and logs
    """
    print(event)
    logs_client = boto3.client("logs")
    # Extract parameters from the body-json structure with fallbacks for different parameter names
    body = event.get("body-json", {})

    since = body.get("since", "4000")
    q_business_application_id = body.get("qbusinessApplicationId") or body.get("applicationId")
    data_source_id = body.get("qdatasourceId") or body.get("datasourceId") or body.get("dataSourceId")

    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(minutes=int(since))).timestamp())

    # Parameters
    log_group_name = f"/aws/qbusiness/{q_business_application_id}"
    log_stream_name = f"{data_source_id}"
    base_query = """fields @ingestionTime, DocumentId, SourceId, Message, @timestamp, AwsAccountId, IndexId, LogLevel, ErrorCode, ErrorMessage, message
        | sort @timestamp desc
        | filter (LogLevel = "Error" or ispresent(ErrorCode)) and ispresent(DocumentId)
      """
    stream_filter = f"  | filter @logStream like /^{log_stream_name}/"
    query = base_query + stream_filter
    print(query)
    try:
        # Start query
        start_query_response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query,
            limit=1000,  # Adjust based on expected log volume
        )

        query_id = start_query_response["queryId"]

        # Wait for query to complete with backoff strategy
        response = None
        max_attempts = 12  # Maximum number of attempts (2 minutes total)
        attempt = 0
        backoff_time = 5  # Start with 5 seconds

        while (response is None or response["status"] == "Running") and attempt < max_attempts:
            attempt += 1
            # Use exponential backoff with a cap
            wait_time = min(backoff_time * (1.5 ** (attempt - 1)), 20)
            print(f"Waiting {wait_time:.1f} seconds for query to complete (attempt {attempt}/{max_attempts})")

            # Use boto3's waiter pattern instead of sleep if possible
            try:
                response = logs_client.get_query_results(queryId=query_id)
            except logs_client.exceptions.ResourceNotFoundException:
                print("Query ID not found")
                break

        if response is None or response["status"] == "Running":
            print("Query timed out or is still running")
            return {
                "statusCode": 408,
                "body": json.dumps(
                    {"error": "Query Timeout", "message": "The CloudWatch Logs query is taking too long to complete"}
                ),
            }

        error_logs = []
        for result in response["results"]:
            ingestion_time = get_field_value(result, "@ingestionTime")
            document_id = get_field_value(result, "DocumentId")
            error_code = get_field_value(result, "ErrorCode")
            error_message = get_field_value(result, "ErrorMessage")
            error_logs.append(
                {
                    "timestamp": ingestion_time,
                    "document_id": document_id,
                    "error_code": error_code,
                    "error_message": error_message,
                }
            )

        print(f"error_logs: {error_logs}")
        return {"statusCode": 200, "body": {"message": "Logs fetched successfully", "logs": error_logs}}

    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": str(e)}


if __name__ == "__main__":
    handler({}, {})
