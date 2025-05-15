import json
import logging
import os
import boto3
import uuid
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
s3_client = boto3.client('s3')
timestream_client = boto3.client('timestream-write')

# Get environment variables
DB_NAME = os.environ.get('TIMESTREAM_DB_NAME')
TABLE_NAME = os.environ.get('TIMESTREAM_TABLE_NAME')


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
        last_modified = response.get('LastModified', datetime.now())

        # Extract file extension
        file_extension = key.split('.')[-1].lower() if '.' in key else 'unknown'

        # Write to Timestream
        write_to_timestream(bucket, key, size, content_type, file_extension, last_modified)

        logger.info(f"File processed successfully: {key}")

    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}")
        raise


def write_to_timestream(bucket, key, size, content_type, file_extension, last_modified):
    current_time = int(datetime.utcnow().timestamp() * 1000)  # Current time in milliseconds

    try:
        # Prepare dimensions (metadata)
        dimensions = [
            {'Name': 'bucket', 'Value': bucket},
            {'Name': 'key', 'Value': key},
            {'Name': 'content_type', 'Value': content_type},
            {'Name': 'file_extension', 'Value': file_extension}
        ]

        # Prepare record values
        records = [
            {
                'Dimensions': dimensions,
                'MeasureName': 'file_size',
                'MeasureValue': str(size),
                'MeasureValueType': 'BIGINT',
                'Time': str(current_time)
            }
        ]

        # Write to Timestream
        response = timestream_client.write_records(
            DatabaseName=DB_NAME,
            TableName=TABLE_NAME,
            Records=records,
            CommonAttributes={
                'TimeUnit': 'MILLISECONDS'
            }
        )

        logger.info(f"Successfully wrote to Timestream: {response}")

        # Also write a record for file type counting
        file_type_dimensions = [
            {'Name': 'file_extension', 'Value': file_extension}
        ]

        file_type_records = [
            {
                'Dimensions': file_type_dimensions,
                'MeasureName': 'file_count',
                'MeasureValue': '1',
                'MeasureValueType': 'BIGINT',
                'Time': str(current_time)
            }
        ]

        timestream_client.write_records(
            DatabaseName=DB_NAME,
            TableName='file_types',  # Use the file types table
            Records=file_type_records,
            CommonAttributes={
                'TimeUnit': 'MILLISECONDS'
            }
        )

    except Exception as e:
        logger.error(f"Error writing to Timestream: {str(e)}")
        raise