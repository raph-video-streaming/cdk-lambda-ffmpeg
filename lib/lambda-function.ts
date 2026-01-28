import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';
import * as path from 'path';

export interface PythonLambdaWithDynamoDbProps {
  functionName: string;
  pythonFilePath: string;
  handler: string;
  dynamoTable: dynamodb.Table;
  environment?: { [key: string]: string };
  timeout?: cdk.Duration;
  memorySize?: number;
}

/*
* Create lambda function to access DynamoDb table
*/

export class PythonLambdaWithDynamoDb extends Construct {
  public readonly lambdaFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: PythonLambdaWithDynamoDbProps) {
    super(scope, id);

    // Create the Lambda function
    this.lambdaFunction = new lambda.Function(this, "MyLambdaDynamoDb", {
      memorySize: props.memorySize || 128,
      timeout: props.timeout || cdk.Duration.seconds(30),
      description: 'lambda function to read dynamodb table',
      functionName: props.functionName,
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: props.handler,
      environment: props.environment,
      code: lambda.Code.fromAsset(props.pythonFilePath), // Path to your Lambda code
    });



    // Grant the Lambda function read/write permissions to the DynamoDB table
    props.dynamoTable.grantReadWriteData(this.lambdaFunction);

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
  }
}
