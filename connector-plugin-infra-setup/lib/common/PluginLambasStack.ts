// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { resolve } from 'path';

import { StackProps } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

import { PluginAction, PluginActionMetadata } from './types';

export interface PluginLambdasStackProps extends StackProps {
  readonly qBusinessApplicationId: string;
  readonly pluginActionsMetadata: Array<PluginActionMetadata>;
}

export class PluginLambdasStack extends cdk.NestedStack {
  readonly pluginActionLambdas: PluginAction[];

  constructor(scope: Construct, id: string, props: PluginLambdasStackProps) {
    super(scope, id, props);
    this.pluginActionLambdas = props.pluginActionsMetadata.map((action) =>
      this.createPluginLambda(action, props),
    );
  }

  private createPluginLambda(
    pluginActionMedata: PluginActionMetadata,
    props: PluginLambdasStackProps,
  ): PluginAction {
    // Validate path to prevent path traversal
    const validPathPrefixes = ['sharepoint/', 'zendesk/', 'servicenow/', 'salesforce/', 'operations/', 'common/'];
    const isValidPath = validPathPrefixes.some((prefix) =>
      pluginActionMedata.path.startsWith(prefix),
    );

    if (!isValidPath) {
      throw new Error(
        `Invalid lambda path: ${pluginActionMedata.path}. Must start with one of: ${validPathPrefixes.join(', ')}`,
      );
    }

    // Create a safe path first, completely separate from path operations
    const safePath = pluginActionMedata.path.replace(/\.\./g, '').replace(/[^a-zA-Z0-9\/_-]/g, '');
    // Then use the safe path in path operations
    const lambdaPath = resolve(__dirname, '../../../plugin/lambdas/', safePath);

    // Verify the path is within the expected directory to prevent path traversal
    const expectedDir = resolve(__dirname, '../../../plugin/lambdas/');
    if (!lambdaPath.startsWith(expectedDir)) {
      throw new Error(
        `Security error: Path traversal attempt detected. Path must be within ${expectedDir}`,
      );
    }

    const createOAuthAppLambda = new lambda.Function(
      this,
      props + 'PluginActionLambda' + pluginActionMedata.name,
      {
        runtime: lambda.Runtime.PYTHON_3_10,
        handler: pluginActionMedata.handler,
        functionName: pluginActionMedata.name,
        code: lambda.Code.fromAsset(lambdaPath, {
          bundling: {
            image: lambda.Runtime.PYTHON_3_10.bundlingImage,
            command: [
              'bash',
              '-c',
              'pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements.txt -t /asset-output && cp lambda_function.py /asset-output/',
            ],
            platform: 'linux/amd64',
          },
        }),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        role: pluginActionMedata.role,
        environment: pluginActionMedata.environmentVars,
      },
    );

    if (pluginActionMedata.roleActions && pluginActionMedata.roleActions.length) {
      createOAuthAppLambda.addToRolePolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: pluginActionMedata.roleActions,
          resources: pluginActionMedata.roleResources,
        }),
      );
    }

    createOAuthAppLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: ['*'],
      }),
    );

    return {
      metadata: pluginActionMedata,
      lambdaFunction: createOAuthAppLambda,
    };
  }
}
