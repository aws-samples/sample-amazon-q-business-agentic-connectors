// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import { QbusinessOperationsPluginLambdasStack } from './qbusiness-operations-plugin-lambdas-stack';
import { ApigwStack } from '../common/ApigwStack';

export interface QBusinessOperationsParentStackProps extends cdk.StackProps {}

export class QBusinessOperationsParentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: QBusinessOperationsParentStackProps) {
    super(scope, id, props);

    const qbusinessApplicationId = new cdk.CfnParameter(this, 'QBusinessPluginApplicationId', {
      type: 'String',
      description: 'Amazon Q Business Application ID where the custom plugin will be created',
    });

    const qbusinessOperationsPluginLambdasStack = new QbusinessOperationsPluginLambdasStack(
      this,
      'QBusinessOperationsParentStack',
      {
        qBusinessApplicationId: qbusinessApplicationId.valueAsString,
      },
    );

    // Create API Gateway stack
    new ApigwStack(this, 'QBusinessOperationsApigwStack', {
      pluginName: 'qbusiness',
      pluginActions: qbusinessOperationsPluginLambdasStack.pluginActionLambdas,
      qBusinessApplicationId: qbusinessApplicationId.valueAsString,
    });
  }
}
