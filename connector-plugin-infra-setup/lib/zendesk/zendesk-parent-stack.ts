// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from 'path';

import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cr from 'aws-cdk-lib/custom-resources';
import { Construct } from 'constructs';

import { ZendeskPluginLambdasStack } from './zendesk-plugin-lambdas-stack';
import { ZendeskStateTableStack } from './zendesk-state-table-stack';
import { ApigwStack } from '../common/ApigwStack';

/**
 * Properties for the ZendeskParentStack
 */
export interface ZendeskParentStackProps extends cdk.StackProps {
  /**
   * Optional bucket name for storing state
   */
  bucketName?: string;
}

/**
 * Parent stack for the Zendesk connector
 */
export class ZendeskParentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ZendeskParentStackProps) {
    super(scope, id, props);

    // Create a CloudFormation parameter for the Q Business Application ID
    const qbusinessApplicationId = new cdk.CfnParameter(this, 'QBusinessPluginApplicationId', {
      type: 'String',
      description: 'Amazon Q Business Application ID where the custom plugin will be created',
    });

    // Create the state table stack
    const stateTableStack = new ZendeskStateTableStack(this, 'ZendeskStateTableStack', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create the Lambda functions stack
    const zendeskPluginLambdasStack = new ZendeskPluginLambdasStack(
      this,
      'ZendeskPluginLambdasStack',
      {
        stateTable: stateTableStack.stateTable,
        qBusinessApplicationId: qbusinessApplicationId.valueAsString,
      },
    );

    // Create the API Gateway stack using the common ApigwStack
    const apiGwStack = new ApigwStack(this, 'ZendeskApigwStack', {
      pluginName: 'zendesk',
      pluginActions: zendeskPluginLambdasStack.pluginActionLambdas,
      qBusinessApplicationId: qbusinessApplicationId.valueAsString,
    });

    // Output the API Gateway URL
    new cdk.CfnOutput(this, 'ApiGatewayEndpoint', {
      value: apiGwStack.url,
      description: 'The API Gateway endpoint URL',
      exportName: 'ZendeskApiGatewayEndpoint',
    });

    // Create a custom resource to update Lambda environment variables
    this.createLambdaEnvUpdater(apiGwStack.url, zendeskPluginLambdasStack.pluginActionLambdas);
  }

  /**
   * Creates a custom resource to update Lambda environment variables
   */
  private createLambdaEnvUpdater(apiGatewayUrl: string, _pluginActions: unknown[]): void {
    // Create a Lambda function for the custom resource
    const updateLambdaEnvFunction = new lambda.Function(this, 'UpdateLambdaEnvFunction', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, 'custom-resources')),
      timeout: cdk.Duration.minutes(5),
      description: 'Updates Lambda environment variables with API Gateway URL',
    });

    // Add permissions to update Lambda functions
    updateLambdaEnvFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['lambda:GetFunctionConfiguration', 'lambda:UpdateFunctionConfiguration'],
        resources: ['*'], // Scope this down in production
      }),
    );

    // Create a log group for the custom resource provider
    const logGroup = new logs.LogGroup(this, 'UpdateLambdaEnvLogGroup', {
      retention: logs.RetentionDays.ONE_WEEK,
    });

    // Create the custom resource provider
    const provider = new cr.Provider(this, 'UpdateLambdaEnvProvider', {
      onEventHandler: updateLambdaEnvFunction,
      logGroup,
    });

    // Get the Lambda function names that need the API Gateway URL
    const lambdaFunctions = [
      'zendesk-create-oauth-app',
      'zendesk-initiate-oauth-flow',
      'zendesk-oauth-callback',
      'zendesk-exchange-auth-code-for-token',
    ];

    // Create the custom resource
    new cdk.CustomResource(this, 'UpdateLambdaEnvResource', {
      serviceToken: provider.serviceToken,
      properties: {
        ApiGatewayUrl: apiGatewayUrl,
        LambdaFunctions: JSON.stringify(lambdaFunctions),
        // Add a timestamp to force update on each deployment
        UpdateTimestamp: new Date().toISOString(),
      },
    });
  }
}
