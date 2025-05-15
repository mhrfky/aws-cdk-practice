#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_file_processing.stacks.storage_stack import StorageStack

app = cdk.App()

# Define environment
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# Create storage stack (S3, SQS)
storage_stack = StorageStack(app, "FileProcessingStorage", env=env)

app.synth()