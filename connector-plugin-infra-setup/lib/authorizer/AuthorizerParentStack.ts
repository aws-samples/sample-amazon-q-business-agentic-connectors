// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

import { AuthorizerStack } from './AuthorizerStack';

export interface AuthorizerParentStackProps extends cdk.StackProps {}

export class AuthorizerParentStack extends cdk.Stack {
  readonly lambdaAuthorizer: lambda.Function;
  readonly requestAuthorizer: apigateway.RequestAuthorizer;

  constructor(scope: Construct, id: string, props: AuthorizerParentStackProps) {
    super(scope, id, props);

    const authorizerStack = new AuthorizerStack(this, 'AuthorizerStack', props);
    this.lambdaAuthorizer = authorizerStack.lambdaAuthorizer;
    this.requestAuthorizer = authorizerStack.requestAuthorizer;
  }
}
