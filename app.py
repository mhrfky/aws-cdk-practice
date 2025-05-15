#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_file_processing.stacks.storage_stack import StorageStack
from aws_file_processing.stacks.processing_lambda_stack import ProcessingLambdaStack
from aws_file_processing.stacks.networking_stack import NetworkingStack
from aws_file_processing.stacks.database_stack import DatabaseStack

app = cdk.App()

# Define environment
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# Create networking stack (VPC, subnets, security groups)
networking_stack = NetworkingStack(app, "FileProcessingNetwork", env=env)

# Create storage stack (S3, SQS)
storage_stack = StorageStack(app, "FileProcessingStorage", env=env)

# Create database stack
database_stack = DatabaseStack(app, "FileProcessingDatabase",
                              vpc=networking_stack.vpc,
                              env=env)

# Create compute stack (Lambda)
compute_stack = ProcessingLambdaStack(app, "FileProcessingCompute",
                                   bucket=storage_stack.bucket,
                                   queue=storage_stack.queue,
                                   vpc=networking_stack.vpc,
                                   lambda_sg=networking_stack.lambda_sg,
                                   timestream_db=database_stack.timestream_db,
                                   timestream_events_table=database_stack.events_table,
                                   timestream_file_types_table=database_stack.file_types_table,
                                   env=env)

app.synth()