# FFmpeg REST API CDK

This repository contains the AWS CDK infrastructure for the FFmpeg REST API, which provides video processing capabilities through AWS Lambda and Step Functions.

![FFmpeg REST API Architecture](ffmpeg-rest-api-architecture.png)

## Architecture Overview

The FFmpeg REST API uses a serverless architecture with the following components:

- **API Gateway**: Secured REST API with token-based authorization
- **Lambda Functions**: 
  - FFmpeg execution with custom FFmpeg layer
  - Step Function job submission
  - Token authorization
  - S3 event processing for automatic video processing
- **Step Functions**: Orchestrates FFmpeg processing workflows
- **S3 Bucket**: Stores input/output files with lifecycle policies
- **CloudFront**: CDN for fast file delivery with Origin Access Control
- **UUID-based Sessions**: Each job gets a unique identifier for file organization

## API Endpoints

The API is secured with a token-based authorizer. All requests must include an `authorizationToken` header.

### FFmpeg Direct Processing
- **Endpoint**: `/ffmpeg`
- **Method**: POST
- **Description**: Direct FFmpeg processing for simple operations
- **Payload**:
```json
{
  "input_files": {
    "in_1": "https://example.com/input.mp4"
  },
  "output_files": {
    "out_1": "output.mp4"
  },
  "ffmpeg_command": "-i {{in_1}} -c:v libx264 -b:v 1M {{out_1}}"
}
```

### FFmpeg Worker (Step Functions)
- **Endpoint**: `/ffmpeg_worker`
- **Method**: POST
- **Description**: Submits FFmpeg jobs through Step Functions for complex workflows
- **Payload**:
```json
{
  "input_files": "https://example.com/input.webm",
  "output_files": "output.mp4",
  "ffmpeg_command": "-i {{input_files}} -c:v libx264 -b:v 500k {{output_files}}",
  "stepFunction": "arn:aws:states:region:account:stateMachine:StepFunctionFFMPEG..."
}
```

**Response**:
```json
{
  "message": "Step Function execution started successfully",
  "executionArn": "arn:aws:states:...",
  "session_uuid": "c3804dc7-1d94-4fe1-a877-83134cd01ca2",
  "input_files": "https://cloudfront.domain/uuid/input.webm",
  "output_files": "https://cloudfront.domain/uuid/output.mp4"
}
```

## Automatic Processing

### S3 Event-Driven Processing

Files uploaded to the S3 bucket with the `import/` prefix automatically trigger FFmpeg processing:

- **Trigger**: Object creation events in S3 with `import/` prefix
- **Expected Path Structure**: `import/{video_id}/{filename}`
- **Processing**: Automatic Step Function execution with predefined FFmpeg settings
- **Output**: Processed files stored in `/ffmpeg/{video_id}/` with CloudFront URLs

### Manual Processing via API

Each FFmpeg job is assigned a unique UUID that:
- Organizes files in S3 under `/ffmpeg/{uuid}/`
- Provides isolated processing environments
- Enables tracking and cleanup of job artifacts
- Creates predictable output URLs

## File Lifecycle

- **Input Files**: Downloaded to `/tmp` in Lambda execution environment
- **Processing**: FFmpeg operations performed in UUID-specific folders
- **Output Files**: Uploaded to S3 with UUID path structure
- **Cleanup**: S3 lifecycle policy automatically deletes files after 7 days
- **Access**: Files served through CloudFront CDN with Origin Access Control

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Node.js and npm installed
3. AWS CDK installed (`npm install -g aws-cdk`)

### Deployment Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd cdk-lambda-ffmpeg
```

2. Install dependencies:
```bash
npm install
```

3. Update the account ID in `bin/cdk-lambda.ts` with your AWS account ID.

4. Bootstrap the CDK environment (if not already done):
```bash
npx cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

5. Deploy the stack:
```bash
npx cdk deploy
```

## FFmpeg Layer Creation

Create the FFmpeg layer for Lambda:

```bash
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz.md5
md5sum -c ffmpeg-release-amd64-static.tar.xz.md5

tar xvf ffmpeg-release-amd64-static.tar.xz
mkdir -p ffmpeg/bin
cp ffmpeg-*-amd64-static/ffprobe ffmpeg/bin 
cp ffmpeg-*-amd64-static/ffmpeg ffmpeg/bin 

# Create layer zip
cd ffmpeg
zip -r ffmpeg_layer.zip .
cd ..
mv ffmpeg/ffmpeg_layer.zip lib/lambda/layer/ffmpeg/
rm -rf ffmpeg ffmpeg-*
```

## Security Features

- **Token-based Authorization**: All API endpoints require valid authorization tokens
- **Origin Access Control**: S3 bucket access restricted to CloudFront
- **Encrypted Storage**: S3 objects encrypted with AWS managed keys
- **VPC Isolation**: Lambda functions can be deployed in VPC for additional security
- **IAM Least Privilege**: Functions have minimal required permissions

## Monitoring and Logging

- **CloudWatch Logs**: All Lambda execution logs
- **Step Function Monitoring**: Visual workflow execution tracking
- **API Gateway Metrics**: Request/response metrics and error rates
- **CloudFront Access Logs**: CDN usage and performance metrics

## Useful Commands

* `npm run build` - Compile TypeScript to JavaScript
* `npm run watch` - Watch for changes and compile
* `npm run test` - Run Jest unit tests
* `npx cdk deploy` - Deploy stack to AWS
* `npx cdk diff` - Compare deployed stack with current state
* `npx cdk synth` - Generate CloudFormation templates
* `npx cdk destroy` - Remove all stack resources