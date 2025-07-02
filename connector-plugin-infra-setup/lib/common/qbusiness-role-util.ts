// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Role } from 'aws-cdk-lib/aws-iam';
import * as iam from 'aws-cdk-lib/aws-iam';

export function addQBusinessPoliciesToRole(role: Role) {
  role.addManagedPolicy(
    iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
  );
  role.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'qbusiness:PutGroup',
        'qbusiness:CreateUser',
        'qbusiness:DeleteGroup',
        'qbusiness:UpdateUser',
        'qbusiness:ListGroups',
        'qbusiness:BatchPutDocument',
        'qbusiness:BatchDeleteDocument',
        'qbusiness:CreateDataSource',
      ],
      resources: [
        'arn:aws:qbusiness:*:*:application/*',
        'arn:aws:qbusiness:*:*:application/*/index/*',
        'arn:aws:qbusiness:*:*:application/*/index/*/data-source/*',
      ],
    }),
  );
  role.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'secretsmanager:GetSecretValue',
        'secretsmanager:CreateSecret',
        'secretsmanager:DescribeSecret',
      ],
      resources: ['arn:aws:secretsmanager:*:*:secret:*'],
    }),
  );
  role.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['s3:GetObject', 's3:ListObjects'],
      resources: ['*'],
    }),
  );
}
