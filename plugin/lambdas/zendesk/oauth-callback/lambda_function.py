# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import html as html_escape  # Import html module for escaping
import json
import os
import time

import boto3

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    """
    Handle OAuth callback from Zendesk
    
    This function processes the OAuth callback from Zendesk, validates the state
    and code parameters, and returns an HTML page that automatically exchanges
    the authorization code for an access token.
    """
    try:
        print(f"Received event: {json.dumps(event)}")

        # Get query parameters - handle both direct and nested formats
        query_params = event.get("queryStringParameters", {}) or {}

        # Check if params are nested in a different structure
        if (not query_params.get("code") or not query_params.get("state")) and event.get("params", {}).get(
            "querystring"
        ):
            print("Using nested query parameters from event.params.querystring")
            query_params = event.get("params", {}).get("querystring", {})

        print(f"Query parameters: {json.dumps(query_params)}")

        code = query_params.get("code")
        state = query_params.get("state")
        error = query_params.get("error")
        error_description = query_params.get("error_description")

        print(f"Code: {code}")
        print(f"State: {state}")

        # Check for errors from Zendesk
        if error:
            error_message = error_description or "OAuth authorization failed"
            return build_error_page(error, error_message)

        # Validate required parameters
        if not code or not state:
            return build_error_page("Bad Request", "Missing required parameters: code, state")

        # Retrieve state from DynamoDB
        state_data = get_state(state)
        if not state_data:
            return build_error_page("Invalid State", "The state parameter is invalid or expired")

        # Check if the state has expired
        now = int(time.time())
        if "expires" in state_data and state_data["expires"] < now:
            return build_error_page("Expired State", "The authorization session has expired")

        # Get the API Gateway URL from environment variables
        api_gateway_url = os.environ.get("API_GATEWAY_URL", "")

        # Return an HTML page that posts the code to the exchange endpoint
        return build_auto_exchange_page(code, state, api_gateway_url)

    except Exception as e:
        print(f"Error: {str(e)}")
        return build_error_page("Server Error", str(e))


def get_state(state):
    """Retrieve state from DynamoDB"""
    table_name = os.environ.get("STATE_TABLE_NAME")
    if not table_name:
        raise ValueError("STATE_TABLE_NAME environment variable not set")

    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"id": state})

    if "Item" not in response:
        return None

    item = response["Item"]

    # Parse the data
    if "data" in item:
        return json.loads(item["data"])

    return item


def build_auto_exchange_page(code, state, api_gateway_url):
    """
    Build an HTML page that automatically exchanges the authorization code for a token
    
    This follows the pattern from the example in the Zendesk connector agent.
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zendesk OAuth Callback</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #333;
            }}
            .loader {{
                border: 5px solid #f3f3f3;
                border-top: 5px solid #3498db;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 2s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .error {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .success {{
                color: #2ecc71;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Zendesk OAuth Authorization</h1>
            <p>Authorization successful! Exchanging code for access token...</p>
            <div class="loader" id="loader"></div>
            <p id="status">Please wait...</p>
        </div>
        
        <script>
            // Function to exchange the code for an access token
            async function exchangeCode() {{
                try {{
                    const apiUrl = '{api_gateway_url}zendesk-exchange-auth-code-for-token';
                    console.log('Exchanging code at URL:', apiUrl);
                    
                    const response = await fetch(apiUrl, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            code: '{code}',
                            state: '{state}'
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        document.getElementById('loader').style.display = 'none';
                        document.getElementById('status').innerHTML = '<span class="success">Success! Token has been stored securely.</span><br><br>You can now close this window and return to Amazon Q Business.';
                    }} else {{
                        document.getElementById('loader').style.display = 'none';
                        document.getElementById('status').innerHTML = '<span class="error">Error: ' + (data.message || 'Failed to exchange code for token') + '</span>';
                        console.error('Error response:', data);
                    }}
                }} catch (error) {{
                    document.getElementById('loader').style.display = 'none';
                    document.getElementById('status').innerHTML = '<span class="error">Error: ' + error.message + '</span>';
                    console.error('Exception:', error);
                }}
            }}
            
            // Exchange the code when the page loads
            window.onload = exchangeCode;
        </script>
    </body>
    </html>
    """

    return {"statusCode": 200, "headers": {"Content-Type": "text/html"}, "body": html, "isBase64Encoded": False}


def build_error_page(title, message):
    """
    Build an HTML error page with proper escaping to prevent XSS
    
    Args:
        title (str): Page title
        message (str): Error message
        
    Returns:
        dict: API Gateway response object
    """
    # Escape user inputs to prevent XSS
    safe_title = html_escape.escape(title)
    safe_message = html_escape.escape(message)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{safe_title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .error {{
                color: #e74c3c;
            }}
            h1 {{
                margin-top: 0;
            }}
        </style>
        <!-- Add Content Security Policy header -->
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'unsafe-inline'">
    </head>
    <body>
        <div class="container">
            <h1 class="error">{safe_title}</h1>
            <p>{safe_message}</p>
        </div>
    </body>
    </html>
    """

    return {
        "statusCode": 400,
        "headers": {
            "Content-Type": "text/html",
            "Content-Security-Policy": "default-src 'self'; style-src 'unsafe-inline'",
            "X-XSS-Protection": "1; mode=block",
            "X-Content-Type-Options": "nosniff",
        },
        "body": html,
        "isBase64Encoded": False,
    }


# For local testing
if __name__ == "__main__":
    os.environ["STATE_TABLE_NAME"] = "zendesk-oauth-state"
    os.environ["API_GATEWAY_URL"] = "https://example.com/prod/"

    test_event = {"queryStringParameters": {"code": "test-auth-code", "state": "test-state"}}

    result = handler(test_event, None)
    print(result)
