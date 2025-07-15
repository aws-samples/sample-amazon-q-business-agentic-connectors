# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import html
import json


def handler(event, context):



    """Function handler."""




    """Function handler."""

    print(f"context: {context}")
    print(f"event: {event}")

    # Safely extract and sanitize user input
    question_from_user = ""
    try:
        if event.get("params", {}).get("querystring", {}).get("question"):
            question_from_user = event["params"]["querystring"]["question"]
            # Escape HTML special characters to prevent XSS
            question_from_user = html.escape(question_from_user)
    except Exception as e:
        print(f"Error extracting question: {str(e)}")
        question_from_user = "[Error: Unable to process question]"

    print(f"Sanitized question: {question_from_user}")

    # Create the help response template without user input
    help_response_template = """
    I am a QSharePoint Helper, a bot that can help setup and manage Q Business - SharePoint Integration. Use the context below to answer user's questions
    <Context>
        I am a QSharePoint Helper, a bot that can help setup and manage Q Business - SharePoint Integration. 
        Here are the high level steps that you have to accomplish in order to setup SharePoint integration with Q Business:
        1. Create an Azure Application in Microsoft Entra Portal. Ensure appropriate permissions are provided to access SharePoint API and Graph API.
        2. Generate a Self Signed Certificate along with Private Key. Upload this certificate to an S3 Bucket and also upload it to the created Azure App.
        3. Create a new QBusiness Data Source under a QBusiness application with sane defaults pointing to the SharePoint URL that you wish to crawl. You will have to create
           Secrets in Secrets Manager that holds the private key and certificate that is stored in a S3 bucket.
        4. Once the data source is created you can manually sync the data source.
        5. I can also help you analyze the last sync run or the errors from your last sync.
        I can help automate any of the above steps.
    </Context>
    
    If the user asks for what limitation you have, you can use the below context
    <Context>
        1. I currently only support certificate-based authentication for SharePoint Online.
        2. I only support Sites.FullControl permission model within Microsoft Entra ID.
        3. I have a set of sane defaults that I use when setting up the QBusiness data sources. You cannot change them through me. However you are free to make changes to the data sources yourself.
    </Context>
    
    Question: {0}
    """

    # Insert the sanitized question into the template
    help_response = help_response_template.replace("{0}", question_from_user)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"{help_response}"}),
        "headers": {
            "Content-Type": "application/json",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
        },
    }
