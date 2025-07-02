// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { NestedStack } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export interface SharepointCertBucketStackProps extends cdk.StackProps {
  bucketName: string;
}

export class SharepointCertBucketStack extends NestedStack {
  readonly certificateBucket: s3.Bucket;
  readonly bucketName: string;

  constructor(scope: Construct, id: string, props: SharepointCertBucketStackProps) {
    super(scope, id, props);
    const uid = cdk.Fn.select(
      0,
      cdk.Fn.split('-', cdk.Fn.select(2, cdk.Fn.split('/', this.stackId))),
    );
    this.certificateBucket = this.createCertificateBucket(props.bucketName + '-' + uid);
    this.bucketName = props.bucketName;
  }

  private createCertificateBucket(bucketName: string): s3.Bucket {
    return new s3.Bucket(this, 'SharepointCertBucketCertStoreId', {
      bucketName,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      lifecycleRules: [
        {
          id: 'DeleteOldVersions',
          enabled: true,
          noncurrentVersionExpiration: cdk.Duration.days(90),
        },
      ],
    });
  }
}
