#!/usr/local/opt/node/bin/node
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { QBusinessOperationsParentStack } from '../lib/qbusinessOps/qbusiness-operations-parent-stack';
import { ServicenowParentStack } from '../lib/servicenow/servicenow-parent-stack';
import { SharepointParentStack } from '../lib/sharepoint/sharepoint-parent-stack';
import { ZendeskParentStack } from '../lib/zendesk/zendesk-parent-stack';

const app = new cdk.App();
const certBucketStore = `sharepoint-cert-${process.env.CDK_DEFAULT_ACCOUNT}-${process.env.CDK_DEFAULT_REGION}`;

new ServicenowParentStack(app, 'ServiceNowStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

new SharepointParentStack(app, 'SharepointStack', {
  bucketName: certBucketStore,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

new QBusinessOperationsParentStack(app, 'QBusinessOperationsStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// Add Zendesk connector stack
new ZendeskParentStack(app, 'ZendeskStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
