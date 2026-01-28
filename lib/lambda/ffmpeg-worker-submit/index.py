import json
import boto3
import uuid
import os

client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    # Generate UUID for this session
    session_uuid = str(uuid.uuid4())
    stepfunctions = boto3.client('stepfunctions')
    s3_hostname = os.environ.get('CLOUDFRONT_HOSTNAME')
    
    # The ARN of the Step Function to execute
    state_machine_arn = event["stepFunction"]
    
    # Convert string inputs to the object format expected by the ffmpeg function
    # Prepend UUID to input files
    input_file=event["input_files"]
    input_video_id = event["video_id"]
    
    input_with_uuid = f"{s3_hostname}/{input_video_id}/{event['input_files']}"
    output_with_uuid = f"{s3_hostname}/ffmpeg/{input_video_id}/{event['output_files']}"
    
    payload = {
        "input_files": input_file,
        "video_id": input_video_id,
        "output_files": {"output_files": event["output_files"]},
        "ffmpeg_command": event["ffmpeg_command"]
    }
    
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
                'session_uuid': session_uuid,
                'input_files': input_file,
                'output_files': output_with_uuid
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }