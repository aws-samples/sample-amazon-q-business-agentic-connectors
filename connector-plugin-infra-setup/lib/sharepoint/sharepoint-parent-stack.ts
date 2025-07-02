// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import { SharepointCertBucketStack } from './sharepoint-cert-bucket-stack';
import { SharepointPluginLambdasStack } from './sharepoint-plugin-lambdas-stack';
import { ApigwStack } from '../common/ApigwStack';

/**
 * Properties for the SharePoint Custom Plugin Infrastructure Stack
 */
export interface SpCustomerPluginInfraStackProps extends cdk.StackProps {
  bucketName: string;
}

export class SharepointParentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SpCustomerPluginInfraStackProps) {
    super(scope, id, props);

    const qbusinessApplicationId = new cdk.CfnParameter(this, 'QBusinessPluginApplicationId', {
      type: 'String',
      description: 'Amazon Q Business Application ID where the custom plugin will be created',
    });

    const certificateBucketStack = new SharepointCertBucketStack(
      this,
      'SharepointCertBucketStackId',
      {
        bucketName: 'qbusiness-sharepoint-certificate-bucket',
      },
    );

    const sharepointPluginLambdasStack = new SharepointPluginLambdasStack(
      this,
      'SharepointPluginLambdasStackId',
      {
        certificateBucket: certificateBucketStack.certificateBucket.bucketName,
        certificateBucketArn: certificateBucketStack.certificateBucket.bucketArn,
        qBusinessApplicationId: qbusinessApplicationId.valueAsString,
      },
    );

    new ApigwStack(this, 'SharepointApigwStack', {
      pluginName: 'sharepoint',
      pluginActions: sharepointPluginLambdasStack.pluginActionLambdas,
      qBusinessApplicationId: qbusinessApplicationId.valueAsString,
    });
  }
}
