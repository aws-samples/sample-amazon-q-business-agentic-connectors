# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

import boto3
import requests

# Initialize AWS clients
secretsmanager = boto3.client("secretsmanager")


def handler(event, context):



    """Function handler."""




    """Function handler for testing Salesforce authentication."""

    try:
        print(f"Received event: {event}")
        
        # Extract parameters from the event
        body = event.get("body-json", {})
        secret_name = body.get("secretName")
        
        # Validate required parameters
        if not secret_name:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Missing required parameter: secretName"
                })
            }
        
        # Retrieve credentials from AWS Secrets Manager
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
        
        # Test authentication using OAuth 2.0 Username-Password flow
        result = test_salesforce_oauth_authentication(credentials)
        
        if result["success"]:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Authentication test successful!",
                    "success": True,
                    "accessToken": f"{result['accessToken'][:10]}...{result['accessToken'][-10:]}",  # Masked for security
                    "instanceUrl": result["instanceUrl"],
                    "userInfo": result.get("userInfo", {}),
                    "tokenType": result.get("tokenType", "Bearer"),
                    "scope": result.get("scope", ""),
                    "secretName": secret_name
                })
            }
        else:
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "message": "Authentication test failed",
                    "success": False,
                    "error": result["error"],
                    "details": result.get("details", "")
                })
            }
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Salesforce API Error",
                "message": str(e)
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



    """Function get_salesforce_credentials."""




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


def test_salesforce_oauth_authentication(credentials):



    """Function test_salesforce_oauth_authentication."""




    """Test Salesforce authentication using OAuth 2.0 Username-Password flow."""
    
    try:
        # OAuth 2.0 Username-Password flow endpoint
        token_url = "https://login.salesforce.com/services/oauth2/token"
        
        # Prepare the OAuth request data
        data = {
            'grant_type': 'password',
            'client_id': credentials['consumerKey'],
            'client_secret': credentials['consumerSecret'],
            'username': credentials['username'],
            'password': f"{credentials['password']}{credentials['securityToken']}"
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        print(f"Testing OAuth authentication with Consumer Key: {credentials['consumerKey'][:10]}...")
        
        # Make the OAuth token request
        response = requests.post(token_url, data=data, headers=headers, timeout=30)
        
        print(f"OAuth response status: {response.status_code}")
        print(f"OAuth response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            access_token = result.get('access_token')
            instance_url = result.get('instance_url')
            token_type = result.get('token_type', 'Bearer')
            scope = result.get('scope', '')
            
            if not access_token or not instance_url:
                return {
                    "success": False,
                    "error": "Invalid OAuth response",
                    "details": "Missing access_token or instance_url in response"
                }
            
            # Get user information to validate the token
            user_info = get_user_info(access_token, instance_url)
            
            return {
                "success": True,
                "accessToken": access_token,
                "instanceUrl": instance_url,
                "tokenType": token_type,
                "scope": scope,
                "userInfo": user_info
            }
        else:
            error_details = response.text
            try:
                error_json = response.json()
                error_details = error_json.get('error_description', error_json.get('error', error_details))
            except:
                pass
            
            return {
                "success": False,
                "error": f"OAuth authentication failed: HTTP {response.status_code}",
                "details": error_details
            }
            
    except Exception as e:
        print(f"Error during authentication test: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": "Exception occurred during authentication test"
        }


def get_user_info(access_token, instance_url):



    """Function get_user_info."""




    """Get user information using the access token to validate authentication."""
    
    try:
        # Query current user information
        query_url = f"{instance_url}/services/data/v60.0/query/"
        query = "SELECT Id, Username, Name, Email, OrganizationId FROM User WHERE Id = UserInfo.getUserId()"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        params = {'q': query}
        response = requests.get(query_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('records') and len(result['records']) > 0:
                user_record = result['records'][0]
                return {
                    "userId": user_record.get('Id'),
                    "username": user_record.get('Username'),
                    "name": user_record.get('Name'),
                    "email": user_record.get('Email'),
                    "organizationId": user_record.get('OrganizationId')
                }
        
        # Fallback: try the identity endpoint
        identity_url = f"{instance_url}/services/oauth2/userinfo"
        response = requests.get(identity_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        
        return {"status": "User info not available"}
        
    except Exception as e:
        print(f"Error getting user info: {str(e)}")
        return {"error": f"Failed to get user info: {str(e)}"}
