import json
import logging
import boto3
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')


def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # Process each SQS message
    for record in event['Records']:
        # Get the S3 event data from SQS message
        body = json.loads(record['body'])
        logger.info(f"Processing message: {json.dumps(body)}")

        # Extract S3 details
        if 'Records' in body:
            for s3_record in body['Records']:
                process_s3_event(s3_record)

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }


def process_s3_event(s3_record):
    # Extract key information
    bucket = s3_record['s3']['bucket']['name']
    key = s3_record['s3']['object']['key']
    size = s3_record['s3']['object'].get('size', 0)

    logger.info(f"Processing file: s3://{bucket}/{key}, Size: {size} bytes")

    try:
        # Get file metadata
        response = s3_client.head_object(Bucket=bucket, Key=key)
        content_type = response.get('ContentType', 'application/octet-stream')
        last_modified = response.get('LastModified', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')

        # Extract file extension
        file_extension = key.split('.')[-1].lower() if '.' in key else 'unknown'

        # Log detailed information
        logger.info(f"File details: Type={content_type}, Extension={file_extension}, Modified={last_modified}")

        # Collect and analyze file statistics (example only)
        file_stats = {
            'bucket': bucket,
            'key': key,
            'size_bytes': size,
            'content_type': content_type,
            'extension': file_extension,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"File statistics: {json.dumps(file_stats)}")

        # In a real application, we would:
        # 1. Write these statistics to Timestream
        # 2. Update counters in Redis
        # These will be implemented when we add the database stack

        logger.info(f"File processed successfully: {key}")

    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}")
        raise