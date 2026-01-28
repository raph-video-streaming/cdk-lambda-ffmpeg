import { join } from "path";
import { Construct } from "constructs";
import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import * as iam from "aws-cdk-lib/aws-iam";
import { 
  aws_cloudfront as cloudfront,
  aws_s3 as s3,
} from "aws-cdk-lib";
//Construct to create a API Gateway using token Authorizer, green Header
interface stepFunctionWorkerConstructProps {
  readonly s3BucketOutput: s3.Bucket;
  readonly cloudFrontOutput: cloudfront.Distribution;
}

export class stepFunctionWorker extends Construct {
  public readonly stepFunctionOutput: sfn.StateMachine;
  constructor(scope: Construct, id: string, props:stepFunctionWorkerConstructProps) {
    super(scope, id);

    /** ------------------ Lambda Handlers Definition ------------------ */

    const submitLambdaName = "ffmpeg-execute";
    const submitLambdaPath = join(
      __dirname,
      "lambda",
      "ffmpeg-execute"
    );
    const myFfmpegLayer = join(
      __dirname,
      "lambda",
      "layer",
      "ffmpeg",
      "ffmpeg_layer.zip"
    );

    const submitLambda = new lambda.Function(this, "SubmitFFMPEG", {
      memorySize: 3008,
      timeout: cdk.Duration.minutes(10),
      description:
        "Function to execute ffmpeg jobs",
      functionName: submitLambdaName,
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "index.lambda_handler",
      code: lambda.Code.fromAsset(submitLambdaPath),
      environment: {
        CLOUDFRONT_HOSTNAME: "https://"+props.cloudFrontOutput.domainName,
        BUCKET_NAME: props.s3BucketOutput.bucketName,
      },
      layers: [
        new lambda.LayerVersion(this, "FFMPEGLayer", {
          code: lambda.Code.fromAsset(myFfmpegLayer),
        }),
      ],
    });

    //Grant permission

    const ffmpegS3Policy = new iam.PolicyStatement({
      actions: ["s3:GetObject", "s3:PutObject", "s3:PutObjectAcl"],
      resources: [props.s3BucketOutput.arnForObjects("*")], // You can scope it down to specific log groups if needed
    });
    // Attach the policy to the Lambda function
    submitLambda.addToRolePolicy(ffmpegS3Policy);

    new cdk.CfnOutput(this, "LambdaArn", {
      value: submitLambda.functionArn,
      description: "The Lambda function ARN",
    });

    /** ------------------ Step functions Definition ------------------ */

    const submitJob = new tasks.LambdaInvoke(this, "Submit Job", {
      lambdaFunction: submitLambda,
      // Lambda's result is in the attribute `Payload`
      outputPath: "$.Payload",
    });

    const jobFailed = new sfn.Fail(this, "Job Failed", {
      cause: "AWS Batch Job Failed",
      error: "DescribeJob returned FAILED",
    });
    const jobSucceeded = new sfn.Succeed(this, "Job Succeeded");

    // Create chain
    const definition = submitJob.next(
      new sfn.Choice(this, "Job Complete?")
        .when(sfn.Condition.numberGreaterThan("$.statusCode", 200), jobFailed)
        .when(sfn.Condition.numberEquals("$.statusCode", 200), jobSucceeded)
    );

    // Create state machine
    this.stepFunctionOutput = new sfn.StateMachine(
      this,
      "FFMPEGWorker",
      {
        definitionBody: sfn.DefinitionBody.fromChainable(definition),
        //timeout: cdk.Duration.minutes(5),
      }
    );

    // Grant lambda execution roles
    submitLambda.grantInvoke(this.stepFunctionOutput.role);

    new cdk.CfnOutput(this, "StepFunction", {
      value: this.stepFunctionOutput.stateMachineName,
      description: "The name of the step function",
    });

    new cdk.CfnOutput(this, "StepFunctionArn", {
      value: this.stepFunctionOutput.stateMachineArn,
      description: "The arn of the step function",
    });

    
  }
}
