// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

import { PluginLambdasStack } from '../common/PluginLambasStack';
import { addQBusinessPoliciesToRole } from '../common/qbusiness-role-util';
import { PluginAction, PluginActionMetadata } from '../common/types';

/**
 * Properties for the SalesforcePluginLambdasStack
 */
export interface SalesforcePluginLambdasStackProps {
  /**
   * The Q Business application ID
   */
  qBusinessApplicationId: string;
}

/**
 * Stack for the Salesforce plugin Lambda functions
 */
export class SalesforcePluginLambdasStack extends cdk.NestedStack {
  /**
   * The plugin action Lambda functions
   */
  public readonly pluginActionLambdas: Array<PluginAction> = [];

  /**
   * The IAM role for the data source
   */
  public readonly dataSourceRole: iam.Role;

  /**
   * The IAM role for the Salesforce Actions Plugin
   */
  public readonly pluginServiceRole: iam.Role;

  constructor(scope: Construct, id: string, props: SalesforcePluginLambdasStackProps) {
    super(scope, id);

    // Create IAM role for data source
    this.dataSourceRole = this.createDataSourceRole();

    // Create IAM role for Salesforce Actions Plugin
    this.pluginServiceRole = this.createPluginServiceRole();

    // Get plugin actions metadata
    const actions = this.getPluginActions();

    // Create the plugin Lambda functions stack
    const pluginLambdasStack = new PluginLambdasStack(this, 'SalesforcePluginLambdasStack', {
      pluginActionsMetadata: actions,
      qBusinessApplicationId: props.qBusinessApplicationId,
    });

    // Store the plugin action Lambda functions
    this.pluginActionLambdas = pluginLambdasStack.pluginActionLambdas;
  }

  /**
   * Create IAM role for the Salesforce data source
   */
  private createDataSourceRole(): iam.Role {
    const role = new iam.Role(this, 'SalesforceDataSourceRole', {
      assumedBy: new iam.ServicePrincipal('qbusiness.amazonaws.com'),
      description: 'IAM role for Salesforce data source in Amazon Q Business',
    });

    // Add Q Business policies
    addQBusinessPoliciesToRole(role);

    // Add Secrets Manager permissions for Salesforce credentials
    role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['secretsmanager:GetSecretValue', 'secretsmanager:DescribeSecret'],
        resources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce-ds-credentials-*`,
        ],
      }),
    );

    return role;
  }

  /**
   * Create IAM role for the Salesforce Actions Plugin
   */
  private createPluginServiceRole(): iam.Role {
    const role = new iam.Role(this, 'SalesforceActionsPluginRole', {
      assumedBy: new iam.ServicePrincipal('qbusiness.amazonaws.com'),
      description: 'IAM role for Salesforce Actions Plugin in Amazon Q Business',
    });

    // Override the default assume role policy with proper conditions
    const trustPolicyDocument = new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          sid: 'QBusinessApplicationTrustPolicy',
          effect: iam.Effect.ALLOW,
          principals: [new iam.ServicePrincipal('qbusiness.amazonaws.com')],
          actions: ['sts:AssumeRole'],
          conditions: {
            StringEquals: {
              'aws:SourceAccount': cdk.Stack.of(this).account,
            },
            ArnLike: {
              'aws:SourceArn': `arn:aws:qbusiness:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:application/*`,
            },
          },
        }),
      ],
    });

    // Apply the custom trust policy
    const cfnRole = role.node.defaultChild as iam.CfnRole;
    cfnRole.assumeRolePolicyDocument = trustPolicyDocument.toJSON();

    // Add Secrets Manager permissions for Salesforce Actions credentials
    role.addToPolicy(
      new iam.PolicyStatement({
        sid: 'AllowQBusinessToGetSecretValue',
        effect: iam.Effect.ALLOW,
        actions: ['secretsmanager:GetSecretValue'],
        resources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce_crm-*`,
        ],
      }),
    );

    return role;
  }

  /**
   * Get plugin actions metadata for Salesforce
   */
  private getPluginActions(): Array<PluginActionMetadata> {
    return [
      {
        name: 'salesforce-helper',
        handler: 'lambda_function.handler',
        path: 'salesforce/helper',
        method: 'GET',
        description: 'Provides guidance and instructions for Salesforce integration',
        roleActions: [],
        roleResources: [],
        environmentVars: {},
      },
      {
        name: 'salesforce-create-connected-app',
        handler: 'lambda_function.handler',
        path: 'salesforce/create-connected-app',
        method: 'POST',
        description: 'Creates a Salesforce Connected App and stores initial credentials securely',
        role: this.createRole('create-connected-app'),
        roleActions: [
          'secretsmanager:CreateSecret',
          'secretsmanager:PutSecretValue',
          'sts:GetCallerIdentity',
        ],
        roleResources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce-ds-credentials-*`,
        ],
        environmentVars: {},
      },
      {
        name: 'salesforce-update-credentials',
        handler: 'lambda_function.handler',
        path: 'salesforce/update-credentials',
        method: 'POST',
        description: 'Updates Salesforce credentials with Consumer Key and Secret after verification',
        role: this.createRole('update-credentials'),
        roleActions: [
          'secretsmanager:GetSecretValue',
          'secretsmanager:PutSecretValue',
          'secretsmanager:UpdateSecret',
          'secretsmanager:DescribeSecret',
        ],
        roleResources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce-ds-credentials-*`,
        ],
        environmentVars: {},
      },
      {
        name: 'salesforce-test-authentication',
        handler: 'lambda_function.handler',
        path: 'salesforce/test-authentication',
        method: 'POST',
        description: 'Tests Salesforce authentication using stored credentials',
        role: this.createRole('test-authentication'),
        roleActions: ['secretsmanager:GetSecretValue', 'secretsmanager:DescribeSecret'],
        roleResources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce-ds-credentials-*`,
        ],
        environmentVars: {},
      },
      {
        name: 'salesforce-create-data-source',
        handler: 'lambda_function.handler',
        path: 'salesforce/create-data-source',
        method: 'POST',
        description: 'Creates a Salesforce data source in Amazon Q Business',
        role: this.createRole('create-data-source'),
        roleActions: [
          'secretsmanager:GetSecretValue',
          'secretsmanager:DescribeSecret',
          'qbusiness:CreateDataSource',
          'qbusiness:StartDataSourceSyncJob',
          'qbusiness:GetDataSource',
          'qbusiness:ListDataSources',
          'iam:PassRole',
          'sts:GetCallerIdentity',
        ],
        roleResources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce-ds-credentials-*`,
          '*', // Q Business resources
          this.dataSourceRole.roleArn,
        ],
        environmentVars: {
          DATA_SOURCE_ROLE_ARN: this.dataSourceRole.roleArn,
        },
      },
      {
        name: 'salesforce-create-salesforce-actions-connected-app',
        handler: 'lambda_function.handler',
        path: 'salesforce/create-salesforce-actions-connected-app',
        method: 'POST',
        description: 'Creates a Salesforce Connected App specifically for Actions integration',
        role: this.createRole('create-salesforce-actions-connected-app'),
        roleActions: [
          'sts:GetCallerIdentity',
        ],
        roleResources: ['*'],
        environmentVars: {},
      },
      {
        name: 'salesforce-setup-salesforce-actions-plugin',
        handler: 'lambda_function.handler',
        path: 'salesforce/setup-salesforce-actions-plugin',
        method: 'POST',
        description: 'Sets up Salesforce Actions Plugin in Q Business with credentials',
        role: this.createRole('setup-salesforce-actions-plugin'),
        roleActions: [
          'secretsmanager:CreateSecret',
          'secretsmanager:PutSecretValue',
          'secretsmanager:DescribeSecret',
          'qbusiness:CreatePlugin',
          'qbusiness:GetPlugin',
          'qbusiness:ListPlugins',
          'iam:CreateRole',
          'iam:AttachRolePolicy',
          'iam:PutRolePolicy',
          'iam:PassRole',
          'sts:GetCallerIdentity',
        ],
        roleResources: [
          `arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:QBusiness-Salesforce_crm-plugin-*`,
          `arn:aws:qbusiness:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:*`, // Q Business resources
          this.pluginServiceRole.roleArn, // IAM roles
        ],
        environmentVars: {
          PLUGIN_SERVICE_ROLE_ARN: this.pluginServiceRole.roleArn,
        },
      },
    ];
  }

  /**
   * Creates a role for a Lambda function
   */
  private createRole(name: string): iam.Role {
    const role = new iam.Role(this, `SalesforceRole${name}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: `Role for Salesforce ${name} Lambda function`,
    });

    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );

    return role;
  }
}
