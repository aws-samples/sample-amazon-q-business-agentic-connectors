// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

import { PluginLambdasStack } from '../common/PluginLambasStack';
import { addQBusinessPoliciesToRole } from '../common/qbusiness-role-util';
import { PluginAction, PluginActionMetadata } from '../common/types';

/**
 * Properties for the ZendeskPluginLambdasStack
 */
export interface ZendeskPluginLambdasStackProps {
  /**
   * The DynamoDB table for storing OAuth state
   */
  stateTable: dynamodb.Table;

  /**
   * The Q Business application ID
   */
  qBusinessApplicationId: string;
}

/**
 * Stack for the Zendesk plugin Lambda functions
 */
export class ZendeskPluginLambdasStack extends cdk.NestedStack {
  /**
   * The plugin action Lambda functions
   */
  public readonly pluginActionLambdas: Array<PluginAction> = [];

  /**
   * The IAM role for the data source
   */
  public readonly dataSourceRole: iam.Role;

  constructor(scope: Construct, id: string, props: ZendeskPluginLambdasStackProps) {
    super(scope, id);

    // Create IAM role for data source
    this.dataSourceRole = this.createDataSourceRole();

    // Get plugin actions metadata
    const actions = this.getPluginActions(props.stateTable);

    // Create Lambda functions using the common PluginLambdasStack
    const lambdasStack = new PluginLambdasStack(this, 'ZendeskLambdaStack', {
      pluginActionsMetadata: actions,
      qBusinessApplicationId: props.qBusinessApplicationId,
    });

    this.pluginActionLambdas = lambdasStack.pluginActionLambdas;
  }

  /**
   * Creates IAM role for Q Business data source
   */
  private createDataSourceRole(): iam.Role {
    const role = new iam.Role(this, 'ZendeskDataSourceRole', {
      assumedBy: new iam.ServicePrincipal('qbusiness.amazonaws.com'),
      description: 'Role for Amazon Q Business Zendesk data source',
    });

    // Add Q Business policies
    addQBusinessPoliciesToRole(role);

    // Add Secrets Manager permissions
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['secretsmanager:GetSecretValue', 'secretsmanager:DescribeSecret'],
        resources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:qbusiness-zendesk-secret-*`,
        ],
      }),
    );

    return role;
  }

  /**
   * Creates a role for a Lambda function
   */
  private createRole(name: string): iam.Role {
    const role = new iam.Role(this, `ZendeskRole${name}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: `Role for Zendesk ${name} Lambda function`,
    });

    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );

    return role;
  }

  /**
   * Gets the plugin actions metadata
   */
  private getPluginActions(stateTable: dynamodb.Table): Array<PluginActionMetadata> {
    return [
      {
        name: 'zendesk-oauth-app-helper',
        handler: 'lambda_function.handler',
        path: 'zendesk/zendesk-oauth-app-helper',
        method: 'GET',
        description: 'Entry point helper for Zendesk connector setup',
        roleActions: [],
        roleResources: [],
        environmentVars: {},
      },
      {
        name: 'zendesk-create-oauth-app',
        handler: 'lambda_function.handler',
        path: 'zendesk/create-zendesk-oauth-app',
        method: 'POST',
        description: 'Creates Zendesk OAuth application configuration',
        role: this.createRole('create-zendesk-oauth-app'),
        roleActions: [],
        roleResources: [],
        environmentVars: {},
      },
      {
        name: 'zendesk-initiate-oauth-flow',
        handler: 'lambda_function.handler',
        path: 'zendesk/initiate-oauth-flow',
        method: 'POST',
        description: 'Initiates OAuth flow with Zendesk',
        role: this.createRole('initiate-oauth-flow'),
        roleActions: ['dynamodb:PutItem', 'dynamodb:GetItem', 'dynamodb:DeleteItem'],
        roleResources: [stateTable.tableArn],
        environmentVars: {
          STATE_TABLE_NAME: stateTable.tableName,
        },
      },
      {
        name: 'zendesk-oauth-callback',
        handler: 'lambda_function.handler',
        path: 'zendesk/oauth-callback',
        method: 'GET',
        description: 'Handles OAuth callback from Zendesk',
        role: this.createRole('oauth-callback'),
        roleActions: ['dynamodb:GetItem', 'dynamodb:DeleteItem'],
        roleResources: [stateTable.tableArn],
        environmentVars: {
          STATE_TABLE_NAME: stateTable.tableName,
        },
        useProxyIntegration: true,
      },
      {
        name: 'zendesk-exchange-auth-code-for-token',
        handler: 'lambda_function.handler',
        path: 'zendesk/exchange-auth-code-for-token',
        method: 'POST',
        description: 'Exchanges authorization code for OAuth token',
        role: this.createRole('exchange-auth-code-for-token'),
        roleActions: [
          'dynamodb:GetItem',
          'dynamodb:DeleteItem',
          'secretsmanager:CreateSecret',
          'secretsmanager:UpdateSecret',
          'secretsmanager:GetSecretValue',
          'secretsmanager:DescribeSecret',
        ],
        roleResources: [
          stateTable.tableArn,
          'arn:aws:secretsmanager:*:*:secret:qbusiness-zendesk-secret-*',
        ],
        environmentVars: {
          STATE_TABLE_NAME: stateTable.tableName,
        },
      },
      {
        name: 'zendesk-create-data-source',
        handler: 'lambda_function.handler',
        path: 'zendesk/create-data-source',
        method: 'POST',
        description: 'Creates data source for Zendesk connection',
        role: this.createRole('create-data-source'),
        roleActions: [
          'secretsmanager:CreateSecret',
          'secretsmanager:UpdateSecret',
          'secretsmanager:GetSecretValue',
          'secretsmanager:DescribeSecret',
          'secretsmanager:ListSecrets',
          'qbusiness:CreateDataSource',
          'qbusiness:DescribeDataSource',
          'qbusiness:DisableAclOnDataSource',
          'iam:PassRole',
        ],
        roleResources: [
          'arn:aws:secretsmanager:*:*:secret:qbusiness-zendesk-secret-*',
          'arn:aws:qbusiness:*:*:application/*',
          this.dataSourceRole.roleArn,
        ],
        environmentVars: {
          DATA_SOURCE_ROLE_ARN: this.dataSourceRole.roleArn,
        },
      },
    ];
  }
}
