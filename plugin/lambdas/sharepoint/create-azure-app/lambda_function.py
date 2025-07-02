# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient


def create_azure_app_with_sites_permission(
    admin_client_id, admin_client_secret, tenant_id, new_app_name, redirect_uris=None
):
    """Function create_azure_app_with_sites_permission."""

    """
    Create a new Azure AD application with Sites.FullControl permission using admin credentials.

    Args:
        admin_client_id (str): Client ID of the admin app with sufficient permissions
        admin_client_secret (str): Client secret of the admin app
        tenant_id (str): Azure AD tenant ID
        new_app_name (str): Name for the new application
        redirect_uris (list, optional): List of redirect URIs for the new app

    Returns:
        dict: Details of the newly created application
    """
    # Create a credential using admin app credentials
    credential = ClientSecretCredential(
        tenant_id=tenant_id, client_id=admin_client_id, client_secret=admin_client_secret
    )

    # Create a Graph client
    graph_client = GraphClient(credential=credential)

    # First, get the Service Principal for Microsoft Graph to find the correct permission ID
    filter_query = "displayName eq 'Microsoft Graph'"
    response = graph_client.get(f"/servicePrincipals?$filter={filter_query}")
    graph_service_principal = response.json()["value"][0]
    graph_sp_id = graph_service_principal["id"]

    sharepoint_filter = "displayName eq 'Office 365 SharePoint Online'"
    sharepoint_response = graph_client.get(f"/servicePrincipals?$filter={sharepoint_filter}")
    sharepoint_sp = sharepoint_response.json()["value"][0]
    sharepoint_sp_id = sharepoint_sp["id"]
    sharepoint_app_id = sharepoint_sp["appId"]  # SharePoint Online App ID

    # Find the Sites.FullControl application permission
    sites_full_control_id = None
    application_full_control_id = None
    sharepoint_sites_full_control_id = None
    app_roles = graph_service_principal.get("appRoles", [])

    for role in app_roles:
        if role["value"] == "Sites.FullControl.All" and "Application" in role["allowedMemberTypes"]:
            sites_full_control_id = role["id"]
            break

    for role in app_roles:
        if role["value"] == "Application.ReadWrite.All" and "Application" in role["allowedMemberTypes"]:
            application_full_control_id = role["id"]
            break

    for role in sharepoint_sp.get("appRoles", []):
        print(f"SharePoint role: {role['value']}")
        if role["value"] == "Sites.FullControl.All" and "Application" in role["allowedMemberTypes"]:
            sharepoint_sites_full_control_id = role["id"]
            break

    print(f"SharePoint APP ID: {sharepoint_app_id}")
    print(f"Graph APP ID: {graph_sp_id}")

    if not sites_full_control_id:
        raise Exception("Could not find Sites.FullControl permission in Microsoft Graph")

    # Prepare the application details with required resource access
    app_data = {
        "displayName": new_app_name,
        "web": {
            "redirectUris": redirect_uris or [],
            "implicitGrantSettings": {"enableAccessTokenIssuance": False, "enableIdTokenIssuance": False},
        },
        "requiredResourceAccess": [
            {
                "resourceAppId": "00000003-0000-0000-c000-000000000000",  # Microsoft Graph App ID
                "resourceAccess": [
                    {"id": sites_full_control_id, "type": "Role"},  # "Role" means Application permission
                    {"id": application_full_control_id, "type": "Role"},  # "Role" means Application permission
                ],
            },
            {
                "resourceAppId": sharepoint_app_id,  # SharePoint Online
                "resourceAccess": [
                    {"id": sharepoint_sites_full_control_id, "type": "Role"}  # "Role" means Application permission
                ],
            },
        ],
    }

    # Create the application
    response = graph_client.post(
        "/applications", data=json.dumps(app_data), headers={"Content-Type": "application/json"}
    )

    app_info = response.json()
    print(f"Application created: {app_info}")

    # Create a service principal for the application
    service_principal_data = {"appId": app_info["appId"]}

    sp_response = graph_client.post(
        "/servicePrincipals", data=json.dumps(service_principal_data), headers={"Content-Type": "application/json"}
    )

    sp_info = sp_response.json()

    # Create a client secret for the application
    password_credential_data = {
        "passwordCredential": {
            "displayName": "Default Client Secret",
            "endDateTime": "2025-12-31T00:00:00Z",  # Set expiry date
        }
    }

    secret_response = graph_client.post(
        f'/applications/{app_info["id"]}/addPassword',
        data=json.dumps(password_credential_data),
        headers={"Content-Type": "application/json"},
    )

    secret_info = secret_response.json()

    # Important note: At this point, the permission is assigned but NOT GRANTED (admin consent required)
    # Return complete information about the new app
    return {
        "object_id": app_info["id"],
        "application_client_id": app_info["appId"],
        "client_secret": secret_info["secretText"],
        "secret_id": secret_info["keyId"],
        "display_name": app_info["displayName"],
        "tenant_id": tenant_id,
        "permission_status": "Sites.FullControl permission has been assigned but requires admin consent",
    }


def createApp(tenantId: str, adminAppId: str, adminSecret: str, clientAppName: str):
    """Function createApp."""

    print("Creating Azure application...")
    print(f"Tenant ID: {tenantId}")
    print(f"Admin App ID: {adminAppId}")
    print(f"Client AppName: {clientAppName}")
    return create_azure_app_with_sites_permission(adminAppId, adminSecret, tenantId, clientAppName)


def construct_url_for_azure_app(appId: str) -> str:
    return f"https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/{appId}/isMSAApp~/false"


def handler(event, context):
    """Function handler."""

    print(f"Received event: {event}")
    app_creation_result = createApp(
        event["body-json"]["tenantId"],
        event["body-json"]["adminAppId"],
        event["body-json"]["adminAppSecret"],
        event["body-json"]["azureAppName"],
    )
    url = construct_url_for_azure_app(app_creation_result.get("application_client_id"))
    return {
        "statusCode": 200,
        "body": f"Azure app created. Here are the details {app_creation_result}. "
        f"Please ensure that you grant admin consent to the created application. "
        f"Go to Azure Portal > Azure Active Directory > App registrations > Find '{app_creation_result['display_name']}' > API permissions > Grant admin consent. "
        f"You can directly navigate to your app from here {url}",
    }


# Example usage
if __name__ == "__main__":
    event = {
        "body-json": {
            "tenantId": "tenant-id-placeholder",
            "azureAppName": "azure-app-name-placeholder",
            "adminAppId": "admin-app-id-placeholder",
            "adminAppSecret": "admin-app-secret-placeholder",
        }
    }
    handler(event, {})
