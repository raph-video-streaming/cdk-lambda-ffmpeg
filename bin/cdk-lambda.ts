#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { CdkFFMpegLambdaStack } from '../lib/cdk-ffmpeg-lambda-stack';
import { Aws} from "aws-cdk-lib";

const app = new cdk.App();

// You need to specify your actual AWS account number here
//const accountId = `${Aws.ACCOUNT_ID}`; // Replace with your actual AWS account ID

const stackName = 'FFmpeg-RestAPI';
const description = 'Rest Api for ffmpeg';

new CdkFFMpegLambdaStack(app, 'CdkFFmpegLambdaStack', {
  stackName: stackName,
  env: {
    region: 'eu-west-1',
    account: `${Aws.ACCOUNT_ID}`,
  },
  description: description
});
