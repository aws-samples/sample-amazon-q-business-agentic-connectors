# A simple request-based authorizer example to demonstrate how to use request
# parameters to allow or deny a request. In this example, a request is
# authorized if the client-supplied headerauth1 header, QueryString1
# query parameter, and stage variable of StageVar1 all match
# specified values of 'headerValue1', 'queryValue1', and 'stageValue1',
# respectively.


def lambda_handler(event, context):
    """Function lambda_handler."""

    print(event)

    # Parse the input for the parameter values
    tmp = event["methodArn"].split(":")
    apiGatewayArnTmp = tmp[5].split("/")
    awsAccountId = tmp[4]
    region = tmp[3]
    restApiId = apiGatewayArnTmp[0]
    stage = apiGatewayArnTmp[1]
    method = apiGatewayArnTmp[2]
    resource = "/"

    if len(apiGatewayArnTmp) > 3:
        resource = apiGatewayArnTmp[3]

    # Always allow access to the OAuth callback and token exchange endpoints
    if resource == "zendesk-oauth-callback" or resource == "zendesk-exchange-auth-code-for-token":
        print(f"Allowing access to {resource} endpoint")
        return generateAllow("me", event["methodArn"])

    # Retrieve request parameters from the Lambda function input:
    headers = event["headers"]

    # Check User-Agent header for authorization
    if headers and "User-Agent" in headers and headers["User-Agent"] == "Apache-HttpClient (Java/17.0.15)":
        print("authorized access")
        response = generateAllow("me", event["methodArn"])
        print(response)
        return response
    else:
        print("unauthorized access")
        return generateDeny("me", event["methodArn"])


# Help function to generate IAM policy
def generatePolicy(principalId, effect, resource):
    """Function generatePolicy."""

    authResponse = {}
    authResponse["principalId"] = principalId
    if effect and resource:
        policyDocument = {}
        policyDocument["Version"] = "2012-10-17"
        policyDocument["Statement"] = []
        statementOne = {}
        statementOne["Action"] = "execute-api:Invoke"
        statementOne["Effect"] = effect
        statementOne["Resource"] = resource
        policyDocument["Statement"] = [statementOne]
        authResponse["policyDocument"] = policyDocument

    authResponse["context"] = {"stringKey": "stringval", "numberKey": 123, "booleanKey": True}

    return authResponse


def generateAllow(principalId, resource):
    """Function generateAllow."""

    return generatePolicy(principalId, "Allow", resource)


def generateDeny(principalId, resource):
    """Function generateDeny."""

    return generatePolicy(principalId, "Deny", resource)
