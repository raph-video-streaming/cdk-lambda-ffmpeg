import { Construct } from "constructs";
import { join } from "path";
import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

//Construct to create a API Gateway using token Authorizer, green Header
interface LambdaApiGatewayConstructProps {
  readonly apiName: string;
  readonly apiDescription: string;
  readonly tokenHeader: string;
}

export class LambdaApi extends Construct {
  public readonly apiLambda: apigateway.RestApi;
  public readonly apiRoot: apigateway.Resource;
  public readonly authorizerToken: apigateway.TokenAuthorizer;

  constructor(
    scope: Construct,
    id: string,
    props: LambdaApiGatewayConstructProps
  ) {
    super(scope, id);

    // Create the API Gateway REST API
    this.apiLambda = new apigateway.RestApi(this, "RestApi", {
      restApiName: props.apiName,
      description: props.apiDescription,
      deployOptions: {
        stageName: "dev",
      },
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL],
      },
      disableExecuteApiEndpoint: false,
      deploy: true,
      retainDeployments: true,
    });

    // Lambda Name
    const functionAuthorizerName = "ffmpeg-auth-api";

    // Path for the lambdas
    const myAuthorizerLambdaFilePath = join(
      __dirname,
      "lambda",
      "ffmpeg-auth"
    );

    // Create new Lambda function to authorize the Lambda
    const authorizerFunction = new lambda.Function(
      this,
      "MyAuthorizerFunction",
      {
        memorySize: 128,
        timeout: cdk.Duration.seconds(30),
        description: "ffmpeg-auth-token-http-header",
        functionName: functionAuthorizerName,
        runtime: lambda.Runtime.PYTHON_3_8,
        handler: "index.lambda_handler",
        code: lambda.Code.fromAsset(myAuthorizerLambdaFilePath), // Path to your Lambda code
      }
    );

    // Create the Lambda authorizer and attach it to the RestApi
    this.authorizerToken = new apigateway.TokenAuthorizer(this, "Authorizer", {
      handler: authorizerFunction,
      identitySource: `method.request.header.${props.tokenHeader}`,
      resultsCacheTtl: cdk.Duration.days(0),
      
    });
    // Set the default authorizer for all methods
    this.apiLambda.root.addMethod("ANY", new apigateway.MockIntegration(), {
      authorizer: this.authorizerToken,
    });


    // Export API Gateway URL
    new cdk.CfnOutput(this, "ApiUrl", {
      value: this.apiLambda.url,
      description: "The API Gateway URL",
  });
  }
}
