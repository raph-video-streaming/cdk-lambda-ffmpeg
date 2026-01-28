import { 
    Aws, 
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    CfnOutput,
    Duration,
    Fn} from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cdk from 'aws-cdk-lib';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

//Construct to create a API Gateway using token Authorizer, green Header
interface apiLambdaIntegationConstructProps {
    readonly LambdaFunctionName: string;
    readonly LambdaFunctionDescription: string;
    readonly LambdaFunctionPath: string;
    readonly LambdaFunctionMemorySize: number;
    readonly LambdaFunctionTimeOut: number;
    readonly LambdaLayerName: string;
    readonly LambdaLayerDescription: string;
    readonly LambdaLayerPath: string;
    readonly s3BucketOutput: s3.Bucket;
    readonly apiGW: apigateway.RestApi;
    readonly apiGWPath: string;
    readonly apiAuthorizer: apigateway.TokenAuthorizer;
    readonly environment?: { [key: string]: string }; 
  }
  
  export class apiLambdaIntegation extends Construct {
    public readonly functionOutput: lambda.Function;
    constructor(
      scope: Construct,
      id: string,
      props: apiLambdaIntegationConstructProps
    ) {
      super(scope, id);
  



    // Create the ApiLambda function
    this.functionOutput = new lambda.Function(this, "MyApiFunction", {
      memorySize: props.LambdaFunctionMemorySize,
      timeout: cdk.Duration.seconds(props.LambdaFunctionTimeOut),
      description: props.LambdaFunctionDescription,
      functionName: props.LambdaFunctionName,
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: "index.lambda_handler",
      environment: props.environment,
      code: lambda.Code.fromAsset(props.LambdaFunctionPath), // Path to your Lambda code
    });
    // Grant the Lambda function write permissions to the S3 bucket
    props.s3BucketOutput.grantWrite(this.functionOutput);

    
 // Conditionally add the Lambda layer if the path is provided
 if (props.LambdaLayerPath && props.LambdaLayerPath.trim() !== '') {
      // Define the Lambda layer with pytz
      const layerLambda = new lambda.LayerVersion(this, props.LambdaLayerName, {
        code: lambda.Code.fromAsset(props.LambdaLayerPath),
        compatibleRuntimes: [lambda.Runtime.PYTHON_3_9],
        description: props.LambdaLayerDescription,
      });

      this.functionOutput.addLayers(layerLambda);
}

    // Adding the Ressource to API Gateway
    const apiItems = props.apiGW.root.addResource(props.apiGWPath);
    const getItemsIntegration = new apigateway.LambdaIntegration(this.functionOutput, {
      proxy: false,
      integrationResponses: [
        {
          statusCode: "200",
          responseTemplates: {
            "application/json": "",
          },
          responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": "'*'",
          },
        },
      ],
    });

    apiItems.addMethod("POST", getItemsIntegration, {
      authorizer: props.apiAuthorizer,
      methodResponses: [
        {
          statusCode: "200",
          responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": true,
          },
          responseModels: {
            "application/json": apigateway.Model.EMPTY_MODEL,
          },
        },
      ],
    });
    //enable pre flight OPTION
    apiItems.addCorsPreflight({
      allowOrigins: ["*"], // Allow all origins
      allowHeaders: ["Content-Type", "AuthorizationToken"],
      allowMethods: ["OPTIONS", "POST"],
    });
    // Export API Gateway URL as CloudFormation output

    new cdk.CfnOutput(this, `ApiURL${props.apiGWPath}`, {
      value: `${props.apiGW.url}${props.apiGWPath}`,
      description: "The URL of the API Gateway endpoint",
    });

  
    }
  }