// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { StackProps } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import { IRole } from 'aws-cdk-lib/aws-iam';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

import { PluginLambdasStack } from '../common/PluginLambasStack';
import { addQBusinessPoliciesToRole } from '../common/qbusiness-role-util';
import { PluginAction, PluginActionMetadata } from '../common/types';

export interface SharepointPluginLambdasStackProps extends StackProps {
  certificateBucket: string;
  certificateBucketArn: string;
  qBusinessApplicationId: string;
}

export class SharepointPluginLambdasStack extends cdk.NestedStack {
  readonly pluginActionLambdas: PluginAction[];
  readonly dataSourceCreateRole: IRole;

  constructor(scope: Construct, id: string, props: SharepointPluginLambdasStackProps) {
    super(scope, id, props);

    this.dataSourceCreateRole = this.createRoleForDataSourceCreation();
    const actions = this.getPluginActions(props);

    const lambdasStack = new PluginLambdasStack(this, 'SharepointLambdaStack', {
      pluginActionsMetadata: actions,
      qBusinessApplicationId: props.qBusinessApplicationId,
    });
    this.pluginActionLambdas = lambdasStack.pluginActionLambdas;
  }

  private getPluginActions(props: SharepointPluginLambdasStackProps): Array<PluginActionMetadata> {
    return [
      {
        name: 'sharepoint-helper',
        handler: 'lambda_function.handler',
        path: 'sharepoint/helper',
        method: 'GET',
        description: 'Answer user question about Sharepoint setup',
        roleActions: [],
        roleResources: [],
        environmentVars: {},
      },
      {
        name: 'sharepoint-create-certificate',
        handler: 'lambda_function.handler',
        path: 'sharepoint/create-certificate',
        method: 'POST',
        description: 'Creates a new certificate',
        roleActions: ['s3:GetObject', 's3:PutObject', 's3:ListBucket'],
        roleResources: [props.certificateBucketArn, props.certificateBucketArn + '/*'],
        environmentVars: {
          CERTIFICATE_BUCKET_NAME: props.certificateBucket,
        },
      },
      {
        name: 'sharepoint-create-azure-app',
        handler: 'lambda_function.handler',
        path: 'sharepoint/create-azure-app',
        method: 'POST',
        description: 'Creates a new Azure app',
        roleActions: [],
        roleResources: [],
        environmentVars: {
          DATA_SOURCE_ROLE_ARN: this.dataSourceCreateRole.roleArn,
        },
      },
      {
        name: 'sharepoint-upload-certificate-to-azure',
        handler: 'lambda_function.handler',
        path: 'sharepoint/upload-certificate-to-azure-app',
        method: 'POST',
        description: 'Uploads certificate from S3Bucket to Azure App',
        roleActions: ['s3:GetObject', 's3:PutObject', 's3:ListBucket'],
        roleResources: [props.certificateBucketArn, props.certificateBucketArn + '/*'],
        environmentVars: {
          CERTIFICATE_BUCKET_NAME: props.certificateBucket,
        },
      },
      {
        name: 'sharepoint-create-data-source',
        handler: 'lambda_function.handler',
        path: 'sharepoint/create-data-source',
        method: 'POST',
        description: 'Creates a new SharePoint dataSource',
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
          'arn:aws:secretsmanager:*:*:secret:qbusiness-sharepoint-secret-*',
          props.certificateBucketArn,
          props.certificateBucketArn + '/*',
          'arn:aws:qbusiness:*:*:application/*',
          this.dataSourceCreateRole.roleArn,
        ],
        environmentVars: {
          DATA_SOURCE_ROLE_ARN: this.dataSourceCreateRole.roleArn,
        },
      },
    ];
  }

  private createRoleForDataSourceCreation() {
    const role = new iam.Role(this, 'SharepointDataSourcePluginRole', {
      assumedBy: new iam.ServicePrincipal('qbusiness.amazonaws.com'),
      description: 'Role for my application',
    });
    addQBusinessPoliciesToRole(role);
    return role;
  }
}
