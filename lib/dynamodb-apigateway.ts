import * as cdk from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";

export interface ApiGatewayDynamoDbProps {
  apiGW: apigateway.RestApi;
  apiGWPath: string;
  tableName: string;
  partitionKey: string;
}

export class ApiGatewayDynamoDb extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string, props: ApiGatewayDynamoDbProps) {
    super(scope, id);

    // Create DynamoDB table with on-demand capacity
    this.table = new dynamodb.Table(this, "Table", {
      tableName: props.tableName,
      partitionKey: {
        name: props.partitionKey,
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Use with caution in production
      timeToLiveAttribute: "TTL",  // Add this line to enable TTL
    });

    // Create IAM role for API Gateway to access DynamoDB
    const role = new iam.Role(this, "ApiGatewayDynamoDBRole", {
      assumedBy: new iam.ServicePrincipal("apigateway.amazonaws.com"),
    });

    // Grant read/write permissions to the role
    this.table.grantReadWriteData(role);

    // Adding the Ressource to API Gateway
    const items = props.apiGW.root.addResource(props.apiGWPath);

// GET (Scan)
items.addMethod(
    "GET",
    new apigateway.AwsIntegration({
      service: "dynamodb",
      action: "Scan",
      options: {
        credentialsRole: role,
        integrationResponses: [
          {
            statusCode: "200",
            responseTemplates: {
              "application/json": "",
            },
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": "'*'",
              "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
              "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
            },
          },
        ],
        requestTemplates: {
          "application/json": JSON.stringify({
            TableName: this.table.tableName,
          }),
        },
      },
    }),
    {
      methodResponses: [
        {
          statusCode: "200",
          responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": true,
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true,
          },
        },
      ],
    }
  );
  
  // Add OPTIONS method for CORS preflight requests
  items.addMethod(
    "OPTIONS",
    new apigateway.MockIntegration({
      integrationResponses: [
        {
          statusCode: "200",
          responseParameters: {
            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
            "method.response.header.Access-Control-Allow-Origin": "'*'",
            "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
          },
        },
      ],
      passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
      requestTemplates: {
        "application/json": '{"statusCode": 200}',
      },
    }),
    {
      methodResponses: [
        {
          statusCode: "200",
          responseParameters: {
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true,
            "method.response.header.Access-Control-Allow-Origin": true,
          },
        },
      ],
    }
  );

    // GET {id} (GetItem)
    const item = items.addResource("{id}");
    item.addMethod(
        "GET",
        new apigateway.AwsIntegration({
          service: "dynamodb",
          action: "GetItem",
          options: {
            credentialsRole: role,
            integrationResponses: [
              {
                statusCode: "200",
                responseTemplates: {
                  "application/json": "",
                },
                responseParameters: {
                  "method.response.header.Access-Control-Allow-Origin": "'*'",
                  "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                  "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
                },
              },
            ],
            requestTemplates: {
              "application/json": JSON.stringify({
                TableName: this.table.tableName,
                Key: {
                  [props.partitionKey]: { S: "$method.request.path.id" },
                },
              }),
            },
          },
        }),
        {
          methodResponses: [
            {
              statusCode: "200",
              responseParameters: {
                "method.response.header.Access-Control-Allow-Origin": true,
                "method.response.header.Access-Control-Allow-Headers": true,
                "method.response.header.Access-Control-Allow-Methods": true,
              },
            },
          ],
        }
      );
      

    new cdk.CfnOutput(this, `ApiURL${props.apiGWPath}`, {
      value: `${props.apiGW.url}${props.apiGWPath}`,
      description: "The URL of the API Gateway endpoint",
    });
  }
}
