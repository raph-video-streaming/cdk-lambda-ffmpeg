import json
import boto3
import uuid
import os
import urllib

client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    # Generate UUID for this session
    session_uuid = str(uuid.uuid4())
    stepfunctions = boto3.client('stepfunctions')
    s3_hostname = os.environ.get('CLOUDFRONT_HOSTNAME')
    
    # The ARN of the Step Function to execute
    state_machine_arn = os.environ.get('STEP_FUNCTION_ARN')
    record = event['Records'][0]

    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(record['s3']['object']['key'])
    base, video_id, filename = key.split("/")

    s3_url = f"s3://{bucket}/{key}"
    print(s3_url)

    # Convert string inputs to the object format expected by the ffmpeg function
    # Prepend UUID to input files
    input_file=s3_url
    output_url = f"{s3_hostname}/ffmpeg/{video_id}/{filename}.mp4"
    ffmpeg_command='-vf "deband=range=16:1thr=0.02:2thr=0.02:3thr=0.02" -c:v libx264 -preset ultrafast -crf 30 -pix_fmt yuv420p -profile:v high -x264-params "psy-rd=1.0:0.15:aq-mode=3:aq-strength=1.0:ref=4:bframes=3" -s 1280x720 -c:a:0 aac -b:a:0 96k {{output_files}}'
    payload = {
        "input_files": input_file,
        "video_id": video_id,
        "output_files": {"output_files": f"{filename}.mp4"},
        "ffmpeg_command": ffmpeg_command
    }
    print("payload",payload)
    try:
        # Start the Step Function execution
        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(payload)
        )
        print(f"Started execution: {response['executionArn']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Step Function execution started successfully',
                'executionArn': response['executionArn'],
                #'session_uuid': session_uuid,
                'input_files': input_file,
                'output_files': output_url
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }