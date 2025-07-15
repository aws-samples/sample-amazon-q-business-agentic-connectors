# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import uuid
import xml.etree.ElementTree as ET

import boto3
import requests

# Initialize AWS clients
secretsmanager = boto3.client("secretsmanager")


def handler(event, context):



    """Function handler."""




    """Function handler for creating Salesforce Connected App."""

    try:
        print(f"Received event: {event}")
        
        # Extract parameters from the event
        body = event.get("body-json", {})
        host_url = body.get("hostUrl")
        username = body.get("username")
        password = body.get("password")
        security_token = body.get("securityToken")
        connected_app_name = body.get("connectedAppName")
        description = body.get("description", "Amazon Q Business Salesforce Connector")
        contact_email = body.get("contactEmail")
        
        # Validate required parameters - contactEmail is now mandatory
        if not all([host_url, username, password, security_token, connected_app_name, contact_email]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Missing required parameters: hostUrl, username, password, securityToken, connectedAppName, contactEmail"
                })
            }
        
        # Clean up host URL
        host_url = host_url.rstrip('/')
        
        # Generate unique identifiers
        app_unique_name = f"{connected_app_name.replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        
        # Create Connected App using Salesforce Metadata API
        result = create_connected_app_with_session_auth(
            username, password, security_token,
            connected_app_name, app_unique_name, description, contact_email
        )
        
        if result["success"]:
            # Store initial credentials in AWS Secrets Manager (without Consumer Key/Secret)
            secret_name = store_initial_salesforce_credentials(
                host_url, username, password, security_token,
                result["callbackUrl"], connected_app_name, app_unique_name
            )
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Connected App created successfully! Please check your email for verification code.",
                    "connectedAppId": result.get("connectedAppId", ""),
                    "connectedAppName": connected_app_name,
                    "secretName": secret_name,
                    "callbackUrl": result["callbackUrl"],
                    "contactEmail": contact_email,
                    "instructions": [
                        "Connected App has been created successfully in Salesforce",
                        f"A verification email has been sent to: {contact_email}",
                        "Next steps:",
                        "1. Check your email for the verification code",
                        "2. Go to Salesforce Setup > App Manager",
                        f"3. Find your Connected App: {connected_app_name}",
                        "4. Click 'View' then 'Manage Consumer Details'",
                        "5. Enter the verification code from your email",
                        "6. Copy the Consumer Key and Consumer Secret",
                        "7. Use the 'Update Salesforce Credentials' function to store them",
                        f"Secret name for next step: {secret_name}"
                    ]
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Connected App Creation Failed",
                    "message": result["error"],
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


def create_connected_app_with_session_auth(username, password, security_token, 
                                         app_name, app_unique_name, description, contact_email):



    """Function create_connected_app_with_session_auth."""




    """Create Connected App using Salesforce session-based authentication."""
    
    try:
        # Step 1: Get session ID using SOAP login
        session_id, server_url = get_session_via_soap_login(username, password, security_token)
        
        # Step 2: Extract instance URL from server URL
        instance_url = server_url.split('/services/')[0]
        
        # Step 3: Create Connected App using Metadata API
        return create_connected_app_via_metadata_api(
            session_id, instance_url, app_name, app_unique_name, description, contact_email
        )
        
    except Exception as e:
        print(f"Error creating Connected App: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": "Failed to create Connected App via Salesforce API"
        }


def get_session_via_soap_login(username, password, security_token):



    """Function get_session_via_soap_login."""




    """Get session ID using SOAP login - most reliable authentication method."""
    
    # SOAP login request
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                      xmlns:urn="urn:enterprise.soap.sforce.com">
        <soapenv:Header/>
        <soapenv:Body>
            <urn:login>
                <urn:username>{username}</urn:username>
                <urn:password>{password}{security_token}</urn:password>
            </urn:login>
        </soapenv:Body>
    </soapenv:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset=UTF-8',
        'SOAPAction': 'login'
    }
    
    # Use login.salesforce.com for authentication
    login_url = "https://login.salesforce.com/services/Soap/c/60.0"
    
    response = requests.post(login_url, data=soap_body, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Parse SOAP response to extract session ID and server URL
    root = ET.fromstring(response.content)
    
    # Handle potential SOAP faults
    fault_elements = root.findall('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
    if fault_elements:
        fault_code = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}faultcode')
        fault_string = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}faultstring')
        error_msg = f"SOAP Fault: {fault_code.text if fault_code is not None else 'Unknown'}"
        if fault_string is not None:
            error_msg += f" - {fault_string.text}"
        raise Exception(error_msg)
    
    # Extract session ID and server URL
    session_id = None
    server_url = None
    
    for elem in root.iter():
        if elem.tag.endswith('sessionId'):
            session_id = elem.text
        elif elem.tag.endswith('serverUrl'):
            server_url = elem.text
    
    if not session_id or not server_url:
        raise Exception("Failed to extract session ID or server URL from SOAP response")
    
    return session_id, server_url


def create_connected_app_via_metadata_api(session_id, instance_url, app_name, app_unique_name, description, contact_email):



    """Function create_connected_app_via_metadata_api."""




    """Create Connected App using Salesforce Metadata API (SOAP)."""
    
    # Determine callback URL based on Salesforce instance type
    callback_url = determine_callback_url(instance_url)
    
    # Use Metadata API for Connected App creation
    metadata_url = f"{instance_url}/services/Soap/m/60.0"
    
    # Create Connected App using SOAP Metadata API
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                      xmlns:met="http://soap.sforce.com/2006/04/metadata">
        <soapenv:Header>
            <met:SessionHeader>
                <met:sessionId>{session_id}</met:sessionId>
            </met:SessionHeader>
        </soapenv:Header>
        <soapenv:Body>
            <met:create>
                <met:metadata xsi:type="met:ConnectedApp" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <met:fullName>{app_unique_name}</met:fullName>
                    <met:label>{app_name}</met:label>
                    <met:description>{description}</met:description>
                    <met:contactEmail>{contact_email}</met:contactEmail>
                    <met:oauthConfig>
                        <met:callbackUrl>{callback_url}</met:callbackUrl>
                        <met:scopes>Full</met:scopes>
                        <met:isIntrospectAllTokens>true</met:isIntrospectAllTokens>
                        <met:isPkceRequired>true</met:isPkceRequired>
                        <met:isSecretRequiredForRefreshToken>true</met:isSecretRequiredForRefreshToken>
                    </met:oauthConfig>
                </met:metadata>
            </met:create>
        </soapenv:Body>
    </soapenv:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset=UTF-8',
        'SOAPAction': 'create'
    }
    
    print(f"Creating Connected App via Metadata API: {app_name} with callback URL: {callback_url}")
    
    response = requests.post(metadata_url, data=soap_body, headers=headers, timeout=30)
    
    print(f"Metadata API response status: {response.status_code}")
    print(f"Metadata API response: {response.text}")
    
    if response.status_code == 200:
        # Parse SOAP response - simplified without polling
        try:
            root = ET.fromstring(response.content)
            
            # Get deployment ID from response
            id_elements = root.findall('.//{http://soap.sforce.com/2006/04/metadata}id')
            connected_app_id = id_elements[0].text if id_elements else ""
            
            return {
                "success": True,
                "connectedAppId": connected_app_id,
                "callbackUrl": callback_url
            }
                
        except ET.ParseError as e:
            return {
                "success": False,
                "error": "Failed to parse Metadata API response",
                "details": str(e)
            }
    else:
        return {
            "success": False,
            "error": f"Metadata API request failed: HTTP {response.status_code}",
            "details": response.text
        }


def determine_callback_url(instance_url):



    """Function determine_callback_url."""




    """Determine the correct callback URL based on Salesforce instance type."""
    
    # Check if this is a sandbox instance
    if 'test.salesforce.com' in instance_url or 'sandbox' in instance_url.lower():
        return "https://test.salesforce.com/services/oauth2/token"
    else:
        # Default to Developer/Production Edition
        return "https://login.salesforce.com/services/oauth2/token"


def store_initial_salesforce_credentials(host_url, username, password, security_token, callback_url, connected_app_name, app_unique_name):



    """Function store_initial_salesforce_credentials."""




    """Store initial Salesforce credentials in AWS Secrets Manager (without Consumer Key/Secret)."""
    
    # Generate a unique secret name
    secret_name = f"qbusiness-salesforce-credentials-{str(uuid.uuid4())[:8]}"
    
    # Prepare the secret value with initial credentials
    secret_value = {
        "hostUrl": host_url,
        "username": username,
        "password": password,
        "securityToken": security_token,
        "authenticationUrl": callback_url,
        "connectedAppName": connected_app_name,
        "appUniqueName": app_unique_name,
        "consumerKey": "",
        "consumerSecret": ""
    }
    
    try:
        # Create the secret in AWS Secrets Manager
        secretsmanager.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret_value),
            Description="Salesforce credentials for Amazon Q Business connector"
        )
        
        print(f"Successfully stored initial credentials in secret: {secret_name}")
        return secret_name
        
    except Exception as e:
        print(f"Error storing credentials in Secrets Manager: {str(e)}")
        raise Exception(f"Failed to store credentials: {str(e)}")
