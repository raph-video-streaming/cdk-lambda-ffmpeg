import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface S3EventLambdaProps {
  functionName: string;
  pythonFilePath: string;
  s3Bucket: s3.Bucket;
  environment?: { [key: string]: string };
  timeout?: cdk.Duration;
  memorySize?: number;
}

export class S3EventLambda extends Construct {
  public readonly lambdaFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: S3EventLambdaProps) {
    super(scope, id);

    // Create the Lambda function
    this.lambdaFunction = new lambda.Function(this, "S3EventLambda", {
      memorySize: props.memorySize || 512,
      timeout: props.timeout || cdk.Duration.seconds(60),
      description: 'Lambda function triggered by S3 events with import prefix',
      functionName: props.functionName,
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.lambda_handler',
      environment: props.environment,
      code: lambda.Code.fromAsset(props.pythonFilePath),
    });

    // Grant the Lambda function permissions to read from S3
    props.s3Bucket.grantRead(this.lambdaFunction);

    // Add Step Functions permissions
    this.lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'states:StartExecution',
        ],
        resources: ['*'], // You may want to scope this down to specific state machines
      })
    );

    // Add CloudWatch Logs permissions
    this.lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'logs:CreateLogGroup',
          'logs:CreateLogStream',
          'logs:PutLogEvents',
        ],
        resources: ['arn:aws:logs:*:*:*'],
      })
    );

    // Add S3 event notification with 'import' prefix filter
    props.s3Bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(this.lambdaFunction),
      { prefix: 'import' }
    );
  }
}