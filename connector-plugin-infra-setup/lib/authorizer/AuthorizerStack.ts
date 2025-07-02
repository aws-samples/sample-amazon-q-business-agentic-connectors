// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { join } from 'path';

import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import { IdentitySource } from 'aws-cdk-lib/aws-apigateway';
import { PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

import { AuthorizerParentStackProps } from './AuthorizerParentStack';

export class AuthorizerStack extends cdk.NestedStack {
  readonly lambdaAuthorizer: lambda.Function;
  readonly requestAuthorizer: apigateway.RequestAuthorizer;

  constructor(scope: Construct, id: string, props: AuthorizerParentStackProps) {
    super(scope, id, props);

    const LambdaAuthorizeRole = new Role(this, 'LambdaAuthorizerRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
    });

    LambdaAuthorizeRole.addToPolicy(
      new PolicyStatement({
        resources: ['*'],
        actions: [
          'logs:CreateLogGroup',
          'logs:CreateLogStream',
          'logs:PutLogEvents',
          'secretsmanager:GetSecretValue',
          'sts:AssumeRole',
        ],
      }),
    );

    this.lambdaAuthorizer = new lambda.Function(this, props + 'AuthorizerLambda', {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'simple-authorizer.lambda_handler',
      functionName: 'simple-authorizer',
      code: lambda.Code.fromAsset(join(__dirname, '../authorizer/lambda'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_10.bundlingImage,
          command: [
            'bash',
            '-c',
            'pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements.txt -t /asset-output && cp simple-authorizer.py /asset-output/',
          ],
          platform: 'linux/amd64',
        },
      }),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      role: LambdaAuthorizeRole,
    });

    this.requestAuthorizer = new apigateway.RequestAuthorizer(this, 'SimpleRequest1Authorizer', {
      handler: this.lambdaAuthorizer,
      identitySources: [IdentitySource.header('authorization')],
    });
  }
}
