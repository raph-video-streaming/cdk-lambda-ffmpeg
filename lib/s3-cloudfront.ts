import {
  Aws,
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as origins,
  aws_s3 as s3,
  aws_s3_deployment as s3deploy,
  CfnOutput,
  Duration,
  Fn,
} from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cdk from "aws-cdk-lib";

//Construct to create a API Gateway using token Authorizer, green Header
interface s3CloudFrontConstructProps {
  readonly s3BucketName: string;
  readonly s3BucketDescription: string;
  readonly CloudFrontDescription: string;
}

export class s3CloudFront extends Construct {
  public readonly s3BucketOutput: s3.Bucket;
  public readonly cloudFrontOutput: cloudfront.Distribution;
  constructor(scope: Construct, id: string, props: s3CloudFrontConstructProps) {
    super(scope, id);

    /*
     * First step: Create S3 bucket for logs and demo hosting website 👇
     */
    // Creating S3 Bucket for demo website 👇
    const s3Bucket = new s3.Bucket(this, "HostingBucket", {
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      bucketName: props.s3BucketName,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(7),
        },
      ],
    });

    // Create Origin Access Control
    const oac = new cloudfront.S3OriginAccessControl(this, 'OAC', {
      description: 'OAC for S3 bucket access'
    });

    const s3origin = origins.S3BucketOrigin.withOriginAccessControl(s3Bucket, {
      originAccessControl: oac
    });

    /*
     * Second step: Create CloudFront Policies and Origins👇
     */
    /*
     * Third step: Create CloudFront Distributions 👇
     */
    // Creating errorResponse 👇
    const errorResponse = [
      {
        httpStatus: 400,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 403,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 404,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 405,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 414,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 416,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 500,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 501,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 502,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 503,
        ttl: Duration.seconds(1),
      },
      {
        httpStatus: 504,
        ttl: Duration.seconds(1),
      },
    ];

    // Create a new cache policy
    const videoCachePolicy = new cloudfront.CachePolicy(
      this,
      "VideoCachePolicy",
      {
        cachePolicyName: "VideoCachePolicy_FFMPEG",
        comment: "Cache policy for video files",
        defaultTtl: Duration.days(1),
        minTtl: Duration.minutes(1),
        maxTtl: Duration.days(365),
        cookieBehavior: cloudfront.CacheCookieBehavior.none(),
        headerBehavior: cloudfront.CacheHeaderBehavior.allowList(
          "Origin",
          "Access-Control-Request-Headers",
          "Access-Control-Request-Method",
          "Content-Type"
        ),
        queryStringBehavior: cloudfront.CacheQueryStringBehavior.none(),
        enableAcceptEncodingBrotli: true,
        enableAcceptEncodingGzip: true,
      }
    );

    const distributionS3 = new cloudfront.Distribution(
      this,
      "DistributionDemo",
      {
        comment: props.CloudFrontDescription,
        defaultRootObject: "",
        enableLogging: true,
        //logBucket: s3hostingBucket,
        logFilePrefix: "ffmpeg-logs/",
        minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2016,
        defaultBehavior: {
          origin: s3origin,
          cachePolicy: videoCachePolicy,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
        additionalBehaviors: {
          "*.mp4": {
            origin: s3origin,
            cachePolicy: videoCachePolicy,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            responseHeadersPolicy: new cloudfront.ResponseHeadersPolicy(this, "VideoResponseHeaders", {
              customHeadersBehavior: {
                customHeaders: [
                  { header: "content-type", value: "video/mp4", override: true }
                ]
              }
            })
          },
          "*.m3u8": {
            origin: s3origin,
            cachePolicy: videoCachePolicy,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            responseHeadersPolicy: new cloudfront.ResponseHeadersPolicy(this, "HLSResponseHeaders", {
              customHeadersBehavior: {
                customHeaders: [
                  { header: "content-type", value: "application/vnd.apple.mpegurl", override: true }
                ]
              }
            })
          },
          "*.aac": {
            origin: s3origin,
            cachePolicy: videoCachePolicy,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            responseHeadersPolicy: new cloudfront.ResponseHeadersPolicy(this, "AudioResponseHeaders", {
              customHeadersBehavior: {
                customHeaders: [
                  { header: "content-type", value: "audio/aac", override: true }
                ]
              }
            })
          }
        },
      }
    );

    /*
     * Final step: Exporting Varibales for Cfn Outputs 👇
     */
    this.s3BucketOutput = s3Bucket;
    this.cloudFrontOutput = distributionS3;

    new CfnOutput(this, "MyCloudFrontS3Hosting", {
      value: "https://" + distributionS3.domainName,
      description: props.CloudFrontDescription,
    });

    new CfnOutput(this, "MyCloudFrontS3Bucket", {
      value: s3Bucket.bucketName,
      description: "S3 bucket name for ffmpeg",
    });
  }
}
