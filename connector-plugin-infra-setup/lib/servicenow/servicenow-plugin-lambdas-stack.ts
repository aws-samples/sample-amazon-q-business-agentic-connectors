// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { StackProps } from 'aws-cdk-lib';
import { IRole } from 'aws-cdk-lib/aws-iam';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

import { PluginLambdasStack } from '../common/PluginLambasStack';
import { addQBusinessPoliciesToRole } from '../common/qbusiness-role-util';
import { PluginAction, PluginActionMetadata } from '../common/types';

export interface ServicenowPluginLambdaStackProps extends StackProps {
  qBusinessApplicationId: string;
}

export class ServicenowPluginLambdasStack extends cdk.NestedStack {
  readonly pluginActionLambdas: PluginAction[];
  readonly dataSourceCreateRole: IRole;

  constructor(scope: Construct, id: string, props: ServicenowPluginLambdaStackProps) {
    super(scope, id, props);

    this.dataSourceCreateRole = this.createRoleForDataSourceCreation();
    const actions = this.getPluginActions();

    const lambdasStack = new PluginLambdasStack(this, 'ServiceNowLambdaStack', {
      pluginActionsMetadata: actions,
      qBusinessApplicationId: props.qBusinessApplicationId,
    });
    this.pluginActionLambdas = lambdasStack.pluginActionLambdas;
  }

  private createRoleForDataSourceCreation(): IRole {
    const role = new iam.Role(this, 'SnowDataSourcePluginRole', {
      roleName: 'snow-plugin-datasource-role', // Optional but recommended for consistency
      assumedBy: new iam.ServicePrincipal('qbusiness.amazonaws.com'),
      description: 'Role for my application',
    });
    addQBusinessPoliciesToRole(role);
    return role;
  }

  private getPluginActions(): Array<PluginActionMetadata> {
    return [
      {
        name: 'snow-helper',
        handler: 'lambda_function.handler',
        path: 'servicenow/helper',
        method: 'GET',
        description: 'Answer user question about servicenow setup',
        roleActions: [],
        roleResources: [],
        environmentVars: {},
      },
      {
        name: 'qbusiness-setup-helper',
        handler: 'lambda_function.handler',
        path: 'common/qbusiness',
        method: 'GET',
        description: 'Fetch QBusiness Application and Index Ids present in the systerm',
        roleActions: ['qbusiness:ListApplications', 'qbusiness:ListIndices'],
        roleResources: ['*', 'arn:aws:qbusiness:*:*:application/*'],
        environmentVars: {},
      },
      {
        name: 'snow-create-oauth-app',
        handler: 'lambda_function.handler',
        path: 'servicenow/create-oauth-app',
        method: 'POST',
        description: 'Create a new OAuth App in ServiceNow',
        role: this.createRole('create-servicenow-oauth-app'),
        roleActions: [],
        roleResources: [],
        environmentVars: {},
      },
      {
        name: 'snow-create-data-source',
        handler: 'lambda_function.handler',
        path: 'servicenow/create-data-source',
        method: 'POST',
        description: 'Create a new QBusiness ServiceNow data source',
        role: this.createRole('create-data-source'),
        roleActions: [
          'secretsmanager:GetSecretValue',
          'secretsmanager:CreateSecret',
          'secretsmanager:DescribeSecret',
          'secretsmanager:UpdateSecret',
          's3:GetObject',
          's3:ListBucket',
          'qbusiness:CreateDataSource',
          'iam:PassRole',
        ],
        roleResources: [
          'arn:aws:secretsmanager:*:*:secret:qbusiness-servicenow-secret-*',
          'arn:aws:qbusiness:*:*:application/*',
          this.dataSourceCreateRole.roleArn,
        ],
        environmentVars: {
          DATA_SOURCE_ROLE_ARN: this.dataSourceCreateRole.roleArn,
        },
      },
    ];
  }

  private createRole(name: string) {
    const role = new iam.Role(this, 'SnowRole' + name, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for my application',
    });
    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );
    return role;
  }
}
