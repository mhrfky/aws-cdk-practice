#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_file_processing.stacks.storage_stack import StorageStack
from aws_file_processing.stacks.processing_lambda_stack import ProcessingLambdaStack
from aws_file_processing.stacks.networking_stack import NetworkingStack
from aws_file_processing.stacks.database_stack import DatabaseStack
from aws_file_processing.stacks.backend_api_stack import BackendApiStack

app = cdk.App()

# Define environment - this is crucial for cross-stack references to work
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# Create each stack separately but in the same environment
networking_stack = NetworkingStack(app, "FileProcessingNetwork", env=env)

storage_stack = StorageStack(app, "FileProcessingStorage", env=env)

database_stack = DatabaseStack(app, "FileProcessingDatabase",
                              vpc=networking_stack.vpc,
                              env=env)

processing_lambda_stack = ProcessingLambdaStack(app, "FileProcessingCompute",
                                              bucket=storage_stack.bucket,
                                              queue=storage_stack.queue,
                                              vpc=networking_stack.vpc,
                                              lambda_sg=networking_stack.lambda_sg,
                                              timestream_db_name=database_stack.database_name,
                                              timestream_events_table_name=database_stack.events_table_name,
                                              timestream_file_types_table_name=database_stack.file_types_table_name,
                                              env=env)

api_stack = BackendApiStack(app, "FileProcessingBackendApi",
                          vpc=networking_stack.vpc,
                          timestream_db_name=database_stack.database_name,
                          timestream_events_table_name=database_stack.events_table_name,
                          timestream_file_types_table_name=database_stack.file_types_table_name,
                          env=env)

# Add explicit dependencies between stacks
storage_stack.add_dependency(networking_stack)
database_stack.add_dependency(networking_stack)
processing_lambda_stack.add_dependency(storage_stack)
processing_lambda_stack.add_dependency(database_stack)
processing_lambda_stack.add_dependency(networking_stack)
api_stack.add_dependency(networking_stack)
api_stack.add_dependency(database_stack)

# Add tags to all stacks for better resource management
for stack in [networking_stack, storage_stack, database_stack, processing_lambda_stack, api_stack]:
    cdk.Tags.of(stack).add("Project", "FileProcessing")
    cdk.Tags.of(stack).add("ManagedBy", "CDK")

app.synth()