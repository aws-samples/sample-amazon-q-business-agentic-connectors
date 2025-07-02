// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// lib/servicenow-oauth-stack.ts
import * as cdk from 'aws-cdk-lib';
import { StackProps } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

import { PluginLambdasStack } from '../common/PluginLambasStack';
import { PluginAction, PluginActionMetadata } from '../common/types';

export interface ServicenowPluginLambdaStackProps extends StackProps {
  qBusinessApplicationId: string;
}

export class QbusinessOperationsPluginLambdasStack extends cdk.NestedStack {
  readonly pluginActionLambdas: PluginAction[];

  constructor(scope: Construct, id: string, props: ServicenowPluginLambdaStackProps) {
    super(scope, id, props);

    const actions = this.getPluginActions();

    const lambdasStack = new PluginLambdasStack(this, 'QBusinessOperationsPluginLambdasStack', {
      pluginActionsMetadata: actions,
      qBusinessApplicationId: props.qBusinessApplicationId,
    });
    this.pluginActionLambdas = lambdasStack.pluginActionLambdas;
  }

  private getPluginActions(): Array<PluginActionMetadata> {
    return [
      {
        name: 'qbusiness-list-applications',
        handler: 'lambda_function.handler',
        path: 'operations/qbusiness-list-applications',
        method: 'GET',
        description:
          'Fetch QBusiness Application and Index data source Ids configured in the account',
        roleActions: [
          'qbusiness:ListApplications',
          'qbusiness:ListIndices',
          'qbusiness:ListDataSources',
        ],
        roleResources: ['*', 'arn:aws:qbusiness:*:*:application/*'],
        environmentVars: {},
      },
      {
        name: 'qbusiness-sync-data-source',
        handler: 'lambda_function.handler',
        path: 'operations/qbusiness-sync-data-source',
        method: 'POST',
        description: 'Sync a QBusiness data source',
        role: this.createRole('sync-data-source'),
        roleActions: ['qbusiness:StartDataSourceSyncJob'],
        roleResources: ['arn:aws:qbusiness:*:*:application/*'],
        environmentVars: {},
      },
      {
        name: 'qbusiness-sync-summary',
        handler: 'lambda_function.handler',
        path: 'operations/qbusiness-sync-summary',
        method: 'POST',
        description: 'Get sync history for a QBusiness data source',
        role: this.createRole('sync-summary'),
        roleActions: ['qbusiness:ListDataSourceSyncJobs'],
        roleResources: ['arn:aws:qbusiness:*:*:application/*'],
        environmentVars: {},
      },
      {
        name: 'qbusiness-analyze-cloudwatch-logs',
        handler: 'lambda_function.handler',
        path: 'operations/qbusiness-analyze-cloudwatch-logs',
        method: 'POST',
        description: 'Analyze CloudWatch logs for a QBusiness data source',
        role: this.createRole('cloudwatch-logs'),
        roleActions: ['logs:StartQuery', 'logs:GetQueryResults'],
        roleResources: ['*'],
        environmentVars: {},
      },
    ];
  }

  private createRole(name: string) {
    const role = new iam.Role(this, 'QBusinessOps' + name, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for my application',
    });
    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );
    return role;
  }
}
