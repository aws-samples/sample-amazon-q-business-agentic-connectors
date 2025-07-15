# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import uuid
import xml.etree.ElementTree as ET

import requests


def handler(event, context):
    """Function handler for creating Salesforce Actions Connected App."""

    try:
        print(f"Received event: {event}")
        
        # Extract parameters from the event
        body = event.get("body-json", {})
        host_url = body.get("hostUrl")
        username = body.get("username")
        password = body.get("password")
        security_token = body.get("securityToken")
        q_business_endpoint = body.get("qBusinessEndpoint")  # New parameter for Q Business endpoint
        connected_app_name = body.get("connectedAppName")
        description = body.get("description", "Amazon Q Business Salesforce Actions Connector")
        contact_email = body.get("contactEmail")
        
        # Validate required parameters
        if not all([host_url, username, password, security_token, q_business_endpoint, contact_email]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Missing required parameters: hostUrl, username, password, securityToken, qBusinessEndpoint, contactEmail"
                })
            }
        
        # Clean up URLs
        host_url = host_url.rstrip('/')
        q_business_endpoint = q_business_endpoint.rstrip('/')
        
        # Construct the redirect URL for Q Business OAuth callback
        redirect_url = f"{q_business_endpoint}/oauth/callback"
        
        # Generate unique identifiers
        app_unique_name = f"{connected_app_name.replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        
        # Create Connected App using Salesforce Metadata API for Actions
        result = create_actions_connected_app_with_session_auth(
            username, password, security_token,
            connected_app_name, app_unique_name, description, contact_email, redirect_url
        )
        
        if result["success"]:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Salesforce Actions Connected App created successfully!",
                    "connectedAppId": result.get("connectedAppId", ""),
                    "connectedAppName": connected_app_name,
                    "redirectUrl": redirect_url,
                    "qBusinessEndpoint": q_business_endpoint,
                    "contactEmail": contact_email,
                    "purpose": "Salesforce Actions",
                    "instructions": [
                        "Salesforce Actions Connected App has been created successfully",
                        "This Connected App is specifically configured for Salesforce Actions",
                        f"Redirect URL configured: {redirect_url}",
                        "Next steps to get Consumer Key and Secret:",
                        "1. Go to Salesforce Setup > App Manager",
                        f"2. Find your Connected App: {connected_app_name}",
                        "3. Click 'View' then click 'Manage Consumer Details' button",
                        "4. A verification code will be sent to your email at this point",
                        "5. Check your email for the verification code",
                        "6. Enter the verification code in Salesforce",
                        "7. Copy the Consumer Key (Client ID) and Consumer Secret",
                        "8. Use 'Setup Salesforce Actions Plugin' with these credentials:",
                        f"   - Client ID: [from Salesforce]",
                        f"   - Client Secret: [from Salesforce]",
                        f"   - Redirect URL: {redirect_url}"
                    ]
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Salesforce Actions Connected App Creation Failed",
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


def create_actions_connected_app_with_session_auth(username, password, security_token, 
                                                 app_name, app_unique_name, description, contact_email, redirect_url):
    """Create Connected App for Salesforce Actions using session-based authentication."""
    
    try:
        # Step 1: Get session ID using SOAP login
        session_id, server_url = get_session_via_soap_login(username, password, security_token)
        
        # Step 2: Extract instance URL from server URL
        instance_url = server_url.split('/services/')[0]
        
        # Step 3: Create Connected App using Metadata API for Actions
        return create_actions_connected_app_via_metadata_api(
            session_id, instance_url, app_name, app_unique_name, description, contact_email, redirect_url
        )
        
    except Exception as e:
        print(f"Error creating Actions Connected App: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": "Failed to create Salesforce Actions Connected App via Salesforce API"
        }


def get_session_via_soap_login(username, password, security_token):
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


def create_actions_connected_app_via_metadata_api(session_id, instance_url, app_name, app_unique_name, description, contact_email, redirect_url):
    """Create Connected App for Salesforce Actions using Salesforce Metadata API (SOAP)."""
    
    # Use Metadata API for Connected App creation
    metadata_url = f"{instance_url}/services/Soap/m/60.0"
    
    # Create Connected App using SOAP Metadata API with Actions-specific configuration
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
                    <met:description>{description} - Configured for Salesforce Actions integration</met:description>
                    <met:contactEmail>{contact_email}</met:contactEmail>
                    <met:oauthConfig>
                        <met:callbackUrl>{redirect_url}</met:callbackUrl>
                        <met:scopes>CustomApplications</met:scopes>
                        <met:scopes>Basic</met:scopes>
                        <met:scopes>Address</met:scopes>
                        <met:scopes>CustomPermissions</met:scopes>
                        <met:scopes>OpenID</met:scopes>
                        <met:scopes>Profile</met:scopes>
                        <met:scopes>RefreshToken</met:scopes>
                        <met:scopes>Wave</met:scopes>
                        <met:scopes>Web</met:scopes>
                        <met:scopes>Phone</met:scopes>
                        <met:scopes>OfflineAccess</met:scopes>
                        <met:scopes>Chatter</met:scopes>
                        <met:scopes>Api</met:scopes>
                        <met:scopes>Eclair</met:scopes>
                        <met:scopes>Email</met:scopes>
                        <met:scopes>Pardot</met:scopes>
                        <met:scopes>Full</met:scopes>
                        <met:isIntrospectAllTokens>false</met:isIntrospectAllTokens>
                        <met:isPkceRequired>false</met:isPkceRequired>
                        <met:isSecretRequiredForRefreshToken>true</met:isSecretRequiredForRefreshToken>
                        <met:isSecretRequiredForTokenExchange>true</met:isSecretRequiredForTokenExchange>
                        <met:isTokenExchangeEnabled>true</met:isTokenExchangeEnabled>
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
    
    print(f"Creating Salesforce Actions Connected App via Metadata API: {app_name} with redirect URL: {redirect_url}")
    
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
                "redirectUrl": redirect_url
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
