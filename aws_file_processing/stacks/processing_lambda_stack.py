from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_lambda_event_sources as lambda_events,
    aws_ec2 as ec2,
)
from constructs import Construct


class ProcessingLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 bucket, queue, vpc, lambda_sg, timestream_db, timestream_events_table,
                 timestream_file_types_table, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for Lambda with fine-grained permissions
        lambda_role = iam.Role(self, "ProcessorLambdaRole",
                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
                               )

        # Add basic Lambda execution permissions
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        # Add VPC access permissions
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
        )

        # Add specific S3 permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    bucket.bucket_arn,
                    f"{bucket.bucket_arn}/*"
                ]
            )
        )

        # Add SQS permissions with specific actions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                resources=[queue.queue_arn]
            )
        )
        # Add Timestream write permissions
        region = Stack.of(self).region
        account = Stack.of(self).account

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "timestream:WriteRecords",
                    "timestream:DescribeTable",
                    "timestream:DescribeDatabase"
                ],
                resources=[
                    f"arn:aws:timestream:{region}:{account}:database/{timestream_db}",
                    f"arn:aws:timestream:{region}:{account}:database/{timestream_db}/table/{timestream_events_table}",
                    f"arn:aws:timestream:{region}:{account}:database/{timestream_db}/table/{timestream_file_types_table}"
                ]
            )
        )

        # Create Lambda function to process SQS messages
        self.processor_lambda = lambda_.Function(self, "FileProcessorFunction",
                                                 runtime=lambda_.Runtime.PYTHON_3_9,
                                                 code=lambda_.Code.from_asset("src/lambda/file_processor"),
                                                 handler="index.handler",
                                                 timeout=Duration.seconds(60),
                                                 environment={
                                                     "SQS_QUEUE_URL": queue.queue_url,
                                                     "BUCKET_NAME": bucket.bucket_name,
                                                     "TIMESTREAM_DB_NAME": timestream_db.database_name,
                                                     "TIMESTREAM_TABLE_NAME": timestream_events_table.table_name,
                                                 },
                                                 role=lambda_role,
                                                 vpc=vpc,
                                                 security_groups=[lambda_sg],
                                                 vpc_subnets=ec2.SubnetSelection(
                                                     subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                                                 )
                                                 )

        # Add SQS as event source for Lambda
        self.processor_lambda.add_event_source(
            lambda_events.SqsEventSource(queue, batch_size=10)
        )