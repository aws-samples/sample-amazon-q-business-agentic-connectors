# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

import boto3


def handler(event, context):
    """Function handler."""

    qbusiness = boto3.client("qbusiness")
    try:
        print("received event", event)
        applications = []
        paginator = qbusiness.get_paginator("list_applications")
        for page in paginator.paginate():
            for app in page["applications"]:
                print("applicationId " + app.get("applicationId"))
                print("applicationName " + app.get("displayName"))
                result = {
                    "qbusinessApplicationId": app.get("applicationId"),
                    "qbusinessApplicationName": app.get("displayName"),
                }
                index_response = qbusiness.list_indices(applicationId=app.get("applicationId"))
                indices = []
                for index in index_response["indices"]:
                    indices.append(index["indexId"])
                result["indices"] = indices
                applications.append(result)

        print(applications)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "applications": applications,
                }
            ),
        }

    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error", "message": str(e)})}


# For local testing only - will not run in Lambda
if __name__ == "__main__":
    handler({}, {})
