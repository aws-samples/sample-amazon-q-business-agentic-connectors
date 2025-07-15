// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import { SalesforcePluginLambdasStack } from './salesforce-plugin-lambdas-stack';
import { ApigwStack } from '../common/ApigwStack';

/**
 * Properties for the SalesforceParentStack
 */
export interface SalesforceParentStackProps extends cdk.StackProps {
  /**
   * Optional bucket name for storing state (not used for Salesforce but kept for consistency)
   */
  bucketName?: string;
}

/**
 * Parent stack for the Salesforce connector
 */
export class SalesforceParentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SalesforceParentStackProps) {
    super(scope, id, props);

    // Create a CloudFormation parameter for the Q Business Application ID
    const qbusinessApplicationId = new cdk.CfnParameter(this, 'QBusinessPluginApplicationId', {
      type: 'String',
      description: 'Amazon Q Business Application ID where the custom plugin will be created',
    });

    // Create the Lambda functions stack
    const salesforcePluginLambdasStack = new SalesforcePluginLambdasStack(
      this,
      'SalesforcePluginLambdasStack',
      {
        qBusinessApplicationId: qbusinessApplicationId.valueAsString,
      },
    );

    // Create the API Gateway stack using the common ApigwStack
    const apiGwStack = new ApigwStack(this, 'SalesforceApigwStack', {
      pluginName: 'salesforce',
      pluginActions: salesforcePluginLambdasStack.pluginActionLambdas,
      qBusinessApplicationId: qbusinessApplicationId.valueAsString,
    });

    // Output the API Gateway URL
    new cdk.CfnOutput(this, 'ApiGatewayEndpoint', {
      value: apiGwStack.url,
      description: 'The API Gateway endpoint URL for Salesforce connector',
      exportName: 'SalesforceApiGatewayEndpoint',
    });

    // Output the data source role ARN
    new cdk.CfnOutput(this, 'DataSourceRoleArn', {
      value: salesforcePluginLambdasStack.dataSourceRole.roleArn,
      description: 'The IAM role ARN for Salesforce data sources',
      exportName: 'SalesforceDataSourceRoleArn',
    });

    // Output useful information for users
    new cdk.CfnOutput(this, 'SalesforceConnectorInfo', {
      value: JSON.stringify({
        apiEndpoint: apiGwStack.url,
        dataSourceRoleArn: salesforcePluginLambdasStack.dataSourceRole.roleArn,
        supportedObjects: [
          'Knowledge Articles',
          'Cases',
          'Opportunities',
          'Accounts',
          'Contacts',
          'Chatter Feeds',
        ],
      }),
      description: 'Salesforce connector configuration information',
    });
  }
}
