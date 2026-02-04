import { Construct } from "constructs";
import { join } from "path";
import { aws_iam as iam } from "aws-cdk-lib";
import * as cdk from "aws-cdk-lib";
import { LambdaApi } from "./authorizer-apigateway";
import { s3CloudFront } from "./s3-cloudfront";
import { apiLambdaIntegation } from "./lambda-post-apigateway";
import { stepFunctionWorker } from "./stepfunction-worker";
import { S3EventLambda } from "./s3-event-lambda";

export class CdkFFMpegLambdaStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    //######  AUTHORIZER API GATEWAY #########
    //1. Creating the API gateway with Authorizer
    const apiGW = new LambdaApi(this, "LambdaApiGateway", {
      apiName: "rest-api",
      apiDescription: "REST API for ffmpeg",
      tokenHeader: "authorizationToken",
    });

    //######  CLOUDFRONT DISTRIBUTION WITH S3 #########
    //2. Creating the S3 Bucket with CloudFront Distrib for accessing all the logs
    const S3BucketCloudFront = new s3CloudFront(this, "S3BucketCloudFront", {
      s3BucketName: `ffmpeg-cdk-lambda-s3cloudfront-${this.account}`,
      s3BucketDescription: "Bucket for ffmpeg REST API",
      CloudFrontDescription: "Distribution to distribute data from ffmpeg REST",
    });



    //######  FFMPEG Transcoder with AWS Lambda and API Gateway #########
    //######  CREATING THE STEP FUNCTION WORKFLOW  #########

    /** ------------------ Creating the Step Function Workflow ------------------ */

    const stepFunction = new stepFunctionWorker(
      this,
      "StepFunctionFFMPEG",{
        s3BucketOutput: S3BucketCloudFront.s3BucketOutput,
        cloudFrontOutput: S3BucketCloudFront.cloudFrontOutput
      }
    );

    /** ------------------ Creating the API path to submit the job ------------------ */

    const submitJobLambdaName = "ffmpeg-worker-submit";
    const submitJobLambdaPath = join(
      __dirname,
      "lambda",
      "ffmpeg-worker-submit"
    );

    const submiJobIntegration = new apiLambdaIntegation(
      this,
      "submiJobApiIntegration",
      {
        LambdaFunctionName: submitJobLambdaName,
        LambdaFunctionDescription:
          "Function for submitting ffmpeg queries through step function",
        LambdaFunctionMemorySize: 2048,
        LambdaFunctionTimeOut: 300,
        LambdaFunctionPath: submitJobLambdaPath,
        LambdaLayerName: "",
        LambdaLayerDescription: "",
        LambdaLayerPath: "",
        s3BucketOutput: S3BucketCloudFront.s3BucketOutput,
        apiGW: apiGW.apiLambda,
        apiGWPath: "ffmpeg_worker",
        apiAuthorizer: apiGW.authorizerToken,
        environment: {
          CLOUDFRONT_HOSTNAME: "https://"+S3BucketCloudFront.cloudFrontOutput.domainName,
          BUCKET_NAME: S3BucketCloudFront.s3BucketOutput.bucketName,
        },
        
      }
    );

    // Grant the Lambda function write permissions to the S3 bucket
    const ffmpegS3Policy = new iam.PolicyStatement({
      actions: ["s3:GetObject", "s3:PutObject", "s3:PutObjectAcl"],
      resources: [S3BucketCloudFront.s3BucketOutput.arnForObjects("*")],
    });
    // Attach the policy to the Lambda function
    submiJobIntegration.functionOutput.addToRolePolicy(ffmpegS3Policy);
    // Grant the Lambda function write permissions to the S3 bucket
    stepFunction.stepFunctionOutput.grantStartExecution(
      submiJobIntegration.functionOutput
    );

    /*
    //######  S3 EVENT LAMBDA FUNCTION #########
    //Creating the S3 event Lambda function
    const s3EventLambdaPath = join(
      __dirname,
      "lambda",
      "ffmpeg-s3-events"
    );

    const s3EventLambda = new S3EventLambda(
      this,
      "S3EventLambda",
      {
        functionName: "ffmpeg-s3-events",
        pythonFilePath: s3EventLambdaPath,
        s3Bucket: S3BucketCloudFront.s3BucketOutput,
        environment: {
          CLOUDFRONT_HOSTNAME: "https://"+S3BucketCloudFront.cloudFrontOutput.domainName,
          BUCKET_NAME: S3BucketCloudFront.s3BucketOutput.bucketName,
          STEP_FUNCTION_ARN: stepFunction.stepFunctionOutput.stateMachineArn,
        },
        timeout: cdk.Duration.seconds(60),
        memorySize: 512,
      }
    );

    // Grant the S3 event Lambda function permissions to start the Step Function
    stepFunction.stepFunctionOutput.grantStartExecution(
      s3EventLambda.lambdaFunction
    );
    */

  }
}
