// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import { ServicenowPluginLambdasStack } from './servicenow-plugin-lambdas-stack';
import { ApigwStack } from '../common/ApigwStack';

export interface ServiceNowStackProps extends cdk.StackProps {}

export class ServicenowParentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ServiceNowStackProps) {
    super(scope, id, props);

    const qbusinessApplicationId = new cdk.CfnParameter(this, 'QBusinessPluginApplicationId', {
      type: 'String',
      // default: 'cf21fc03-2187-433c-bdbc-488ba5c1076b',
      description: 'Amazon Q Business Application ID where the custom plugin will be created',
    });

    const servicenowOauthStack = new ServicenowPluginLambdasStack(this, 'ServicenowParentStack', {
      qBusinessApplicationId: qbusinessApplicationId.valueAsString,
    });

    new ApigwStack(this, 'ServicenowApigwStack', {
      pluginName: 'servicenow',
      pluginActions: servicenowOauthStack.pluginActionLambdas,
      qBusinessApplicationId: qbusinessApplicationId.valueAsString,
    });
  }
}
