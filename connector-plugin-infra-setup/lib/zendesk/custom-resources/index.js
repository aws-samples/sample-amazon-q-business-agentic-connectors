exports.handler = async function(event) {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    // Extract properties from the event
    const { RequestType, ResourceProperties } = event;
    const { ApiGatewayUrl, LambdaFunctions } = ResourceProperties;
    
    // Skip processing for Delete events
    if (RequestType === 'Delete') {
      return await sendResponse(event, 'SUCCESS', {});
    }
    
    // Parse the Lambda functions list
    const lambdaFunctions = JSON.parse(LambdaFunctions);
    
    // Initialize AWS Lambda client
    const AWS = require('aws-sdk');
    const lambda = new AWS.Lambda();
    
    // Update each Lambda function's environment variables
    for (const functionName of lambdaFunctions) {
      console.log(`Updating environment variables for Lambda: ${functionName}`);
      
      // Get the current configuration
      const config = await lambda.getFunctionConfiguration({
        FunctionName: functionName
      }).promise();
      
      // Get current environment variables or initialize empty object
      const currentEnv = config.Environment?.Variables || {};
      
      // Update environment variables
      await lambda.updateFunctionConfiguration({
        FunctionName: functionName,
        Environment: {
          Variables: {
            ...currentEnv,
            API_GATEWAY_URL: ApiGatewayUrl
          }
        }
      }).promise();
      
      console.log(`Successfully updated environment for ${functionName}`);
    }
    
    return await sendResponse(event, 'SUCCESS', {
      Message: `Updated ${lambdaFunctions.length} Lambda functions with API Gateway URL`
    });
  } catch (error) {
    console.error('Error:', error);
    return await sendResponse(event, 'FAILED', { Error: String(error) });
  }
};

// Helper function to send response to CloudFormation
async function sendResponse(event, status, data) {
  const responseBody = JSON.stringify({
    Status: status,
    Reason: `See the details in CloudWatch Log Stream: ${process.env.AWS_LAMBDA_LOG_STREAM_NAME}`,
    PhysicalResourceId: event.LogicalResourceId,
    StackId: event.StackId,
    RequestId: event.RequestId,
    LogicalResourceId: event.LogicalResourceId,
    Data: data,
  });
  
  console.log('Response Body:', responseBody);
  
  const https = require('https');
  const url = require('url');
  
  const parsedUrl = url.parse(event.ResponseURL);
  const options = {
    hostname: parsedUrl.hostname,
    port: 443,
    path: parsedUrl.path,
    method: 'PUT',
    headers: {
      'content-type': '',
      'content-length': responseBody.length,
    },
  };
  
  return new Promise((resolve, reject) => {
    const request = https.request(options, (response) => {
      console.log(`Status code: ${response.statusCode}`);
      resolve(null);
    });
    
    request.on('error', (error) => {
      console.error('Error sending response:', error);
      reject(error);
    });
    
    request.write(responseBody);
    request.end();
  });
}
