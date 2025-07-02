// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as fs from 'node:fs';
import * as path from 'node:path';
import { join } from 'path';

import * as cdk from 'aws-cdk-lib';
import { Duration, StackProps } from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import {
  AuthorizationType,
  IdentitySource,
  RequestValidator,
  RestApi,
} from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import { PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as qbusiness from 'aws-cdk-lib/aws-qbusiness';
import { Construct } from 'constructs';
import * as yaml from 'js-yaml';

import { PluginAction } from './types';

export interface ApigwStackProps extends StackProps {
  readonly pluginName: string;
  readonly pluginActions: Array<PluginAction>;
  readonly qBusinessApplicationId: string;
}

export class ApigwStack extends cdk.NestedStack {
  private readonly api: apigateway.RestApi;
  private readonly requestAuthorizer: apigateway.RequestAuthorizer;

  // Add a getter for the API URL
  public get url(): string {
    return this.api.url;
  }

  constructor(scope: Construct, id: string, props: ApigwStackProps) {
    super(scope, id, props);

    this.api = this.createApiGateway(props);
    const getRequestValidator = this.createRequestValidator(props.pluginName, this.api, 'GET');
    const postRequestValidator = this.createRequestValidator(props.pluginName, this.api, 'POST');
    this.requestAuthorizer = this.createRequestAuthorizer(props.pluginName);
    this.createApiEndpoints(
      props.pluginActions,
      this.requestAuthorizer,
      getRequestValidator,
      postRequestValidator,
      this.api,
    );
    this.configureApiUsage();
    const pluginRole = this.createPluginRole(props);
    const customPlugin = this.createQBusinessPlugin(props);
    this.createStackOutputs(customPlugin, pluginRole);
  }

  private createApiGateway(props: ApigwStackProps): apigateway.RestApi {
    return new apigateway.RestApi(this, props.pluginName + '-Apigw', {
      restApiName: props.pluginName + ' Plugin Connector API',
      description: 'API for ' + props.pluginName + ' connector operations',
      deployOptions: {
        stageName: 'prod',
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
        tracingEnabled: true, // Enable X-Ray tracing
      },
      cloudWatchRole: true,
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL],
      },
      minimumCompressionSize: 1024, // Enable compression for responses > 1KB
    });
  }

  private createApiEndpoints(
    pluginActions: Array<PluginAction>,
    authorizer: apigateway.RequestAuthorizer,
    getRequestValidator: RequestValidator,
    postRequestValidator: RequestValidator,
    _restApi: RestApi, // Prefix with underscore to indicate it's intentionally unused
  ): void {
    // Create error response model
    const errorResponseModel = this.createErrorResponseModel();

    // Create integration and method responses
    const integrationResponses = this.createIntegrationResponses();
    const methodResponses = this.createMethodResponses(errorResponseModel);

    // Load request template
    const requestTemplate = fs.readFileSync(
      path.join(__dirname, '../templates/request-template.vtl'),
      'utf8',
    );

    for (const pluginAction of pluginActions) {
      const resource = this.api.root.addResource(pluginAction.metadata.name);
      const method = pluginAction.metadata.method;

      // Check if this endpoint should use proxy integration
      if (pluginAction.metadata.useProxyIntegration) {
        // Use proxy integration for endpoints that need to return HTML directly
        resource.addMethod(
          method,
          new apigateway.LambdaIntegration(pluginAction.lambdaFunction, {
            proxy: true, // Use proxy integration
          }),
          {
            methodResponses: [
              {
                statusCode: '200',
                responseParameters: {
                  'method.response.header.Content-Type': true,
                  'method.response.header.Access-Control-Allow-Origin': true,
                },
              },
              {
                statusCode: '400',
                responseParameters: {
                  'method.response.header.Content-Type': true,
                  'method.response.header.Access-Control-Allow-Origin': true,
                },
              },
            ],
            authorizer: authorizer,
            authorizationType: AuthorizationType.CUSTOM,
            requestValidator: method === 'GET' ? getRequestValidator : postRequestValidator,
          },
        );
      } else {
        // Use custom integration for regular API endpoints
        resource.addMethod(
          method,
          new apigateway.LambdaIntegration(pluginAction.lambdaFunction, {
            proxy: false,
            passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
            requestTemplates: {
              'application/json': requestTemplate,
            },
            integrationResponses,
          }),
          {
            methodResponses: methodResponses,
            authorizer: authorizer,
            authorizationType: AuthorizationType.CUSTOM,
            requestValidator: method === 'GET' ? getRequestValidator : postRequestValidator,
          },
        );
      }
    }
  }

  private createRequestAuthorizer(pluginName: string): apigateway.RequestAuthorizer {
    const LambdaAuthorizeRole = new Role(this, 'LambdaAuthorizerRole' + pluginName, {
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

    const lambdaAuthorizer = new lambda.Function(this, pluginName + 'AuthorizerLambda', {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'simple-authorizer.lambda_handler',
      functionName: 'simple-authorizer-' + pluginName,
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

    return new apigateway.RequestAuthorizer(this, 'SimpleRequestAuthorizer-' + pluginName, {
      handler: lambdaAuthorizer,
      identitySources: [IdentitySource.header('User-Agent')],
      resultsCacheTtl: Duration.seconds(0),
    });
  }

  private createRequestValidator(
    pluginName: string,
    restApi: RestApi,
    method: string,
  ): RequestValidator {
    if (method === 'POST') {
      return new RequestValidator(this, 'ReqVal' + pluginName + '-' + method, {
        restApi: restApi,
        requestValidatorName: 'POST-' + pluginName,
        validateRequestBody: true,
      });
    }
    return new RequestValidator(this, 'ReqVal' + pluginName + '-' + method, {
      restApi: restApi,
      requestValidatorName: 'GET-' + pluginName,
    });
  }

  /**
   * Creates error response model for API Gateway
   */
  private createErrorResponseModel(): apigateway.Model {
    return this.api.addModel('ErrorResponseModel', {
      contentType: 'application/json',
      modelName: 'ErrorResponse',
      schema: {
        schema: apigateway.JsonSchemaVersion.DRAFT4,
        title: 'errorResponse',
        type: apigateway.JsonSchemaType.OBJECT,
        properties: {
          message: { type: apigateway.JsonSchemaType.STRING },
          code: { type: apigateway.JsonSchemaType.STRING },
        },
      },
    });
  }

  /**
   * Creates integration responses for API Gateway
   */
  private createIntegrationResponses(): apigateway.IntegrationResponse[] {
    return [
      {
        statusCode: '200',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': "'*'",
        },
      },
      {
        statusCode: '400',
        selectionPattern: '.*[Bad Request].*',
        responseTemplates: {
          'application/json': JSON.stringify({ message: 'Bad Request', code: '400' }),
        },
      },
      {
        statusCode: '500',
        selectionPattern: '.*[Internal Server Error].*',
        responseTemplates: {
          'application/json': JSON.stringify({ message: 'Internal Server Error', code: '500' }),
        },
      },
    ];
  }

  /**
   * Creates method responses for API Gateway
   */
  private createMethodResponses(errorResponseModel: apigateway.Model): apigateway.MethodResponse[] {
    return [
      {
        statusCode: '200',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
        },
      },
      {
        statusCode: '400',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
        },
        responseModels: {
          'application/json': errorResponseModel,
        },
      },
      {
        statusCode: '500',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
        },
        responseModels: {
          'application/json': errorResponseModel,
        },
      },
    ];
  }

  /**
   * Configures API usage plan with throttling and quotas
   */
  private configureApiUsage(): void {
    const plan = this.api.addUsagePlan('SnowonnectorUsagePlan', {
      name: 'Standard',
      throttle: {
        rateLimit: 10,
        burstLimit: 20,
      },
      quota: {
        limit: 1000,
        period: apigateway.Period.MONTH,
      },
    });

    plan.addApiStage({
      stage: this.api.deploymentStage,
    });
  }

  private createPluginRole(props: ApigwStackProps): iam.Role {
    const role = new iam.Role(this, props + '-PluginRole', {
      assumedBy: new iam.ServicePrincipal('qbusiness.amazonaws.com'),
      description: 'Role for Amazon Q Business Snow custom plugin',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['execute-api:Invoke'],
        resources: [`${this.api.arnForExecuteApi()}/*/*/*`],
      }),
    );

    return role;
  }

  private createQBusinessPlugin(props: ApigwStackProps): qbusiness.CfnPlugin {
    // Validate plugin name to prevent path traversal
    const validPluginNames = ['sharepoint', 'zendesk', 'servicenow', 'qbusiness'];
    if (!validPluginNames.includes(props.pluginName)) {
      throw new Error(
        `Invalid plugin name: ${props.pluginName}. Must be one of: ${validPluginNames.join(', ')}`,
      );
    }

    // Create a safe filename first, completely separate from path operations
    const safeFileName = props.pluginName + '_spec.yaml';
    // Then use the safe filename in path operations
    const schemaPath = join(__dirname, '../../../plugin/openApi/', safeFileName);

    // Verify the path is within the expected directory to prevent path traversal
    const expectedDir = join(__dirname, '../../../plugin/openApi/');
    if (!schemaPath.startsWith(expectedDir)) {
      throw new Error(
        `Security error: Path traversal attempt detected. Path must be within ${expectedDir}`,
      );
    }

    const schema = yaml.load(fs.readFileSync(schemaPath, 'utf8')) as Record<string, unknown>;
    // Update schema with API Gateway URL
    const url = this.api.url.replace(/\/$/, '');
    console.log('API GW URL', url);
    schema.servers = [
      {
        url: url,
        description: 'API Gateway endpoint',
      },
    ];

    return new qbusiness.CfnPlugin(this, props.pluginName + '-ConnectorPlugin', {
      applicationId: props.qBusinessApplicationId,
      type: 'CUSTOM',
      displayName: props.pluginName + 'ConnectorPlugin',
      authConfiguration: {
        noAuthConfiguration: {},
      },
      customPluginConfiguration: {
        apiSchemaType: 'OPEN_API_V3',
        apiSchema: {
          payload: yaml.dump(schema),
        },
        description:
          'Custom plugin for ' + props.pluginName + ' integration with Amazon Q Business',
      },
    });
  }

  private createStackOutputs(customPlugin: qbusiness.CfnPlugin, datasourceRole: Role): void {
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'API Gateway endpoint URL',
      exportName: `${this.stackName}-ApiUrl`,
    });

    new cdk.CfnOutput(this, 'PluginId', {
      value: customPlugin.attrPluginId,
      description: 'Amazon Q Business Plugin ID',
      exportName: `${this.stackName}-PluginId`,
    });

    new cdk.CfnOutput(this, 'DataSourceRoleArn', {
      value: datasourceRole.roleArn,
      description: 'ARN of the IAM role for Q Business data source',
      exportName: `${this.stackName}-DataSourceRoleArn`,
    });
  }
}
