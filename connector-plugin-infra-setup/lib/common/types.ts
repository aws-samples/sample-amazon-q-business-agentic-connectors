// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export interface PluginAction {
  readonly metadata: PluginActionMetadata;
  readonly lambdaFunction: lambda.Function;
}

export interface PluginActionMetadata {
  readonly name: string;
  readonly handler: string;
  readonly path: string;
  readonly method: string;
  readonly description: string;
  readonly roleActions: string[];
  readonly roleResources: string[];
  readonly role?: iam.IRole;
  readonly environmentVars: Record<string, string>;
  readonly useProxyIntegration?: boolean;
}
