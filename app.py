#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_file_processing.stacks.storage_stack import StorageStack as StorageNestedStack
from aws_file_processing.stacks.processing_lambda_stack import ProcessingLambdaStack as ProcessingLambdaNestedStack
from aws_file_processing.stacks.networking_stack import NetworkingStack as NetworkingNestedStack
from aws_file_processing.stacks.database_stack import DatabaseStack as DatabaseNestedStack
from aws_file_processing.stacks.backend_api_stack import BackendApiStack

app = cdk.App()

# Define environment
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# Create main parent stack
main_stack = cdk.Stack(app, "FileProcessingMainStack", env=env)

# Create networking nested stack
networking_stack = NetworkingNestedStack(main_stack, "FileProcessingNetwork")

# Create storage nested stack
storage_stack = StorageNestedStack(main_stack, "FileProcessingStorage")

# Create database nested stack
database_stack = DatabaseNestedStack(main_stack, "FileProcessingDatabase",
                                    vpc=networking_stack.vpc)

# Create compute nested stack
processing_lambda_stack = ProcessingLambdaNestedStack(main_stack, "FileProcessingCompute",
                                                    bucket=storage_stack.bucket,
                                                    queue=storage_stack.queue,
                                                    vpc=networking_stack.vpc,
                                                    lambda_sg=networking_stack.lambda_sg,
                                                    timestream_db_name=database_stack.database_name,
                                                    timestream_events_table_name=database_stack.events_table_name,
                                                    timestream_file_types_table_name=database_stack.file_types_table_name)

# Create backend API nested stack
api_stack = BackendApiStack(main_stack, "FileProcessingBackend",
                          vpc=networking_stack.vpc,
                          timestream_db_name=database_stack.database_name,
                          timestream_events_table_name=database_stack.events_table_name,
                          timestream_file_types_table_name=database_stack.file_types_table_name)
# Note: Removed the env parameter since it's not needed for nested stacks

app.synth()