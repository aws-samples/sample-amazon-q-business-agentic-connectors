# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

import boto3


def handler(event, context):



    """Function handler."""




    """Function handler."""

    qbusiness = boto3.client("qbusiness")
    try:
        print(f"received event: {event}")
        applications = []
        application_paginator = qbusiness.get_paginator("list_applications")
        data_sources_paginator = qbusiness.get_paginator("list_data_sources")

        for page in application_paginator.paginate():
            for app in page["applications"]:
                print(f'applicationId: {app.get("applicationId")}')
                print(f'applicationName: {app.get("displayName")}')

                result = {
                    "qbusinessApplicationId": app.get("applicationId"),
                    "qbusinessApplicationName": app.get("displayName"),
                }

                index_response = qbusiness.list_indices(applicationId=app.get("applicationId"))
                indices = []

                for index in index_response["indices"]:
                    data_sources = []
                    for data_source_page in data_sources_paginator.paginate(
                        applicationId=app.get("applicationId"), indexId=index["indexId"]
                    ):
                        for data_source in data_source_page.get("dataSources", []):
                            data_source_info = {
                                "dataSourceName": data_source.get("displayName"),
                                "dataSourceId": data_source.get("dataSourceId"),
                                "dataSourceType": data_source.get("type"),
                                "dataSourceStatus": data_source.get("status"),
                            }
                            data_sources.append(data_source_info)

                    index_info = {"indexId": index["indexId"], "dataSources": data_sources}
                    indices.append(index_info)

                result["indices"] = indices
                applications.append(result)

        print(f"Found {len(applications)} applications")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "applications": applications,
                }
            ),
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error", "message": str(e)})}


# For local testing only - will not run in Lambda
if __name__ == "__main__":
    handler({}, {})
