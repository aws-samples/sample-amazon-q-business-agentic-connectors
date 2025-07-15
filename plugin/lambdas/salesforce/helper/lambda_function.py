# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json


def handler(event, context):



    """Function handler."""




    """Function handler for Salesforce helper."""

    try:
        print(f"Received event: {event}")
        
        # Get the question from query parameters
        question = event.get("params", {}).get("querystring", {}).get("question", "")
        
        # Provide comprehensive guidance for Salesforce integration
        response = {
            "message": "Welcome to the Amazon Q Business Salesforce Connector! I'll help you set up a secure connection to your Salesforce instance.",
            "instructions": [
                "1. Gather your Salesforce credentials:",
                "   - Salesforce instance URL (e.g., https://mycompany.salesforce.com)",
                "   - Admin username and password",
                "   - Security token (from Salesforce Settings > My Personal Information > Reset My Security Token)",
                "",
                "2. Create a Connected App:",
                "   - Use the 'Create Salesforce Connected App' action",
                "   - This will automatically create a Connected App in your Salesforce org",
                "   - You'll receive Consumer Key and Consumer Secret",
                "",
                "3. Test Authentication:",
                "   - Use the 'Test Salesforce Authentication' action",
                "   - This validates all credentials work together",
                "",
                "4. Create Data Source:",
                "   - Use the 'Create Salesforce Data Source' action",
                "   - Configure which Salesforce objects to include",
                "   - The system will create a secure secret in AWS Secrets Manager"
            ],
            "requirements": [
                "Salesforce System Administrator access",
                "Salesforce Developer Edition or higher (for API access)",
                "Valid Salesforce username, password, and security token",
                "Amazon Q Business application and index already created"
            ],
            "nextSteps": [
                "Start by using the 'Create Salesforce Connected App' action",
                "Have your Salesforce credentials ready",
                "Ensure you have System Administrator privileges in Salesforce"
            ]
        }
        
        # Provide specific guidance based on the question
        if question:
            question_lower = question.lower()
            if "credential" in question_lower or "password" in question_lower:
                response["message"] = "For Salesforce credentials, you need: username, password, security token, and instance URL. The security token can be reset from Salesforce Settings."
            elif "connected app" in question_lower or "consumer" in question_lower:
                response["message"] = "The Connected App will be created automatically using Salesforce APIs. You'll receive the Consumer Key and Consumer Secret needed for authentication."
            elif "security token" in question_lower:
                response["message"] = "To get your security token: Go to Salesforce Setup > My Personal Information > Reset My Security Token. Check your email for the new token."
            elif "error" in question_lower or "fail" in question_lower:
                response["message"] = "Common issues: Invalid credentials, expired security token, insufficient permissions, or API limits. Use the test authentication feature to diagnose problems."
        
        return {
            "statusCode": 200,
            "body": json.dumps(response)
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
