# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import html
import json


def handler(event, context):
    """Function handler."""

    print(f"context {context}")
    print(f"event {event}")

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
    I am QZendesk Helper, a bot that can help setup and manage Q Business - Zendesk Integration. Use the context below to answer user's questions
    <Context>
        I am QZendesk Helper, a bot that can help setup and manage Q Business - Zendesk Integration. 
        Here are the high level steps that you have to accomplish in order to setup Zendesk integration with Q Business:
        1. Create an OAuth application in your Zendesk account using the automated setup
        2. Complete the OAuth flow to authenticate with Zendesk
        3. Create a new Zendesk data source in QBusiness
        4. Once the data source is created you can manually sync the data source
        5. I can also help you analyze the last sync run or the errors from your last sync
        I can help automate all of these steps for you.
    </Context>
    
    If the user asks about the automated OAuth app setup, use the below context:
    <Context>
        For the automated OAuth app setup, you'll need:
        - Your Zendesk subdomain (e.g., "mycompany" for mycompany.zendesk.com)
        - Admin email address with admin privileges in Zendesk
        - An API token (can be created in Zendesk Admin Center > APIs > API tokens)
        - App Name (Name for Oauth App to be created in Zendesk portal)  
        
        I'll use these credentials to create the OAuth app via the Zendesk API, configure the proper redirect URIs,
        and set up the necessary scopes for Amazon Q Business integration.
    </Context>
    
    If the user mentions that authorization is already done or completed or authorization successful, use the below context:
    <Context>
        Great! Since the OAuth authorization is already completed, we can proceed directly to creating a Zendesk data source in Amazon Q Business.
        
        To create a Zendesk data source, you'll need:
        - Your Amazon Q Business application ID
        - Your Amazon Q Business index ID
        - Your Zendesk subdomain
        - A name for your data source (optional)
        - The type of Zendesk data you want to index (Guide articles, Support tickets, or both)
        
        I'll help you set up the data source with the appropriate configuration for your needs.
    </Context>
    
    If the user asks about data source creation, use the below context:
    <Context>
        To create a Zendesk data source in Amazon Q Business, you'll need:
        - A completed OAuth flow with a valid access token
        - Your Amazon Q Business application ID
        - Your Amazon Q Business index ID
        - The type of Zendesk data you want to index (Guide articles, Support tickets, or both)
        
        I'll help you set up the data source with the appropriate configuration for your needs.
    </Context>
    
    If the user asks about limitations, use the below context:
    <Context>
        1. I only support OAuth 2.0 authentication for Zendesk integration
        2. I use a set of default configurations when setting up the QBusiness data sources. While you can't modify these defaults through me, you can make changes to the data sources directly in the Amazon Q Business console
        3. The Zendesk integration supports indexing Guide articles and Support tickets
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
