import json
import os
import boto3
import subprocess
import urllib.request
import uuid
from urllib.parse import urlparse

def lambda_handler(event, context):
    bucket_name = os.environ.get('BUCKET_NAME')
    s3_hostname = os.environ.get('CLOUDFRONT_HOSTNAME')
    s3_client = boto3.client('s3')
    
    try:
        # Parse the payload
        input_files = event.get('input_files', {})
        output_files = event.get('output_files', {})
        ffmpeg_command = event.get('ffmpeg_command', '')
        
        print(f"Received input_files: {input_files}")
        print(f"Received output_files: {output_files}")
        print(f"Received ffmpeg_command: {ffmpeg_command}")
        
        if not input_files or not output_files or not ffmpeg_command:
            return {
                'statusCode': 400,
                'body': 'Missing required fields: input_files, output_files, or ffmpeg_command'
            }
        
        # Extract UUID from the first input file URL
        first_input_url = list(input_files.values())[0]
        parsed_url = urlparse(first_input_url)
        path_parts = parsed_url.path.strip('/').split('/')
        session_uuid = path_parts[0] if path_parts else str(uuid.uuid4())
        
        session_folder = f"/tmp/{session_uuid}"
        os.makedirs(session_folder, exist_ok=True)
        print(f"Using session UUID: {session_uuid}")
        print(f"Created session folder: {session_folder}")
        
        # Download input files to /tmp
        local_inputs = {}
        for key, url in input_files.items():
            local_path = f"/tmp/{key}_{os.path.basename(urlparse(url).path)}"
            print(f"Downloading {url} to {local_path}")
            urllib.request.urlretrieve(url, local_path)
            local_inputs[key] = local_path
            print(f"Downloaded {key}: {local_path}")
        
        # Prepare output file paths in session folder
        local_outputs = {}
        for key, filename in output_files.items():
            local_outputs[key] = f"{session_folder}/{filename}"
        
        # Replace placeholders in ffmpeg command
        cmd = ffmpeg_command
        for key, path in local_inputs.items():
            cmd = cmd.replace(f"{{{{{key}}}}}", path)
        for key, path in local_outputs.items():
            cmd = cmd.replace(f"{{{{{key}}}}}", path)
        
        # Execute ffmpeg command
        full_cmd = f"ffmpeg {cmd}"
        print(f"Executing: {full_cmd}")
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        
        print(f"FFmpeg return code: {result.returncode}")
        print(f"FFmpeg stdout: {result.stdout}")
        if result.stderr:
            print(f"FFmpeg stderr: {result.stderr}")
        
        if result.returncode != 0:
            return {
                'statusCode': 500,
                'body': f'FFmpeg error: {result.stderr}'
            }
        
        # Upload session folder to S3
        output_urls = {}
        for key, local_path in local_outputs.items():
            if os.path.exists(local_path):
                s3_key = f'ffmpeg/{session_uuid}/{output_files[key]}'
                print(f"Uploading {local_path} to s3://{bucket_name}/{s3_key}")
                s3_client.upload_file(local_path, bucket_name, s3_key)
                output_urls[key] = f"{s3_hostname}/{s3_key}"
                print(f"Uploaded {key}: {output_urls[key]}")
            else:
                print(f"Output file not found: {local_path}")
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'FFmpeg processing completed successfully',
                'session_uuid': session_uuid,
                'output_files': output_urls,
                'ffmpeg_stdout': result.stdout
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }