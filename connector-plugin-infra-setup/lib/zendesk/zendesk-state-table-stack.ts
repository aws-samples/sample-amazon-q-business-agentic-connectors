// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

/**
 * Properties for the ZendeskStateTableStack
 */
export interface ZendeskStateTableStackProps {
  /**
   * The removal policy for the DynamoDB table
   */
  removalPolicy?: cdk.RemovalPolicy;
}

/**
 * Stack for the Zendesk state table
 */
export class ZendeskStateTableStack extends Construct {
  /**
   * The DynamoDB table for storing OAuth state
   */
  public readonly stateTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: ZendeskStateTableStackProps = {}) {
    super(scope, id);

    // Create DynamoDB table for state management
    this.stateTable = new dynamodb.Table(this, 'StateTable', {
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: true,
      removalPolicy: props.removalPolicy || cdk.RemovalPolicy.RETAIN,
      timeToLiveAttribute: 'expires', // Enable TTL on the expires attribute
    });
  }
}
