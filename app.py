#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_file_processing.stacks.storage_stack import StorageStack
from aws_file_processing.stacks.processing_lambda_stack import ProcessingLambdaStack
from aws_file_processing.stacks.networking_stack import NetworkingStack
from aws_file_processing.stacks.database_stack import DatabaseStack
from aws_file_processing.stacks.backend_api_stack import BackendApiStack
# If you split the backend stack as suggested:
# from aws_file_processing.stacks.backend_infra_stack import BackendInfrastructureStack
# from aws_file_processing.stacks.backend_service_stack import BackendServiceStack

app = cdk.App()

# Define environment
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# Create independent stacks instead of nested stacks
# This allows CloudFormation to deploy them in parallel where possible

# Create networking stack (foundation for other stacks)
networking_stack = NetworkingStack(app, "FileProcessingNetworkStack", env=env)

# Create storage stack (independent of networking)
storage_stack = StorageStack(app, "FileProcessingStorageStack", env=env)

# Create database stack (depends on networking)
database_stack = DatabaseStack(app, "FileProcessingDatabaseStack",
                              env=env,
                              vpc=networking_stack.vpc)

# Create compute stack (depends on storage, networking, and database)
processing_lambda_stack = ProcessingLambdaStack(app, "FileProcessingComputeStack",
                                               env=env,
                                               bucket=storage_stack.bucket,
                                               queue=storage_stack.queue,
                                               vpc=networking_stack.vpc,
                                               lambda_sg=networking_stack.lambda_sg,
                                               timestream_db_name=database_stack.database_name,
                                               timestream_events_table_name=database_stack.events_table_name,
                                               timestream_file_types_table_name=database_stack.file_types_table_name)

# Add explicit dependencies
processing_lambda_stack.add_dependency(networking_stack)
processing_lambda_stack.add_dependency(storage_stack)
processing_lambda_stack.add_dependency(database_stack)

# Create backend API stack (depends on networking and database)
# Option 1: Keep as a single stack
api_stack = BackendApiStack(app, "FileProcessingBackendStack",
                           env=env,
                           vpc=networking_stack.vpc,
                           timestream_db_name=database_stack.database_name,
                           timestream_events_table_name=database_stack.events_table_name,
                           timestream_file_types_table_name=database_stack.file_types_table_name)

api_stack.add_dependency(networking_stack)
api_stack.add_dependency(database_stack)



app.synth()