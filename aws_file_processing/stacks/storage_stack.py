from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_s3_notifications as s3n,
)

from constructs import Construct

class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope,construct_id, **kwargs)


        # Create S3 Bucket
        self.bucket = s3.Bucket(self, "FileUploadBucket",
                                versioned = True,
                                encryption = s3.BucketEncryption.S3_MANAGED,
                                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                removal_policy = RemovalPolicy.DESTROY)

        # Create SQS Queue
        self.queue = sqs.Queue(self, "FileUploadQueue",
            visibility_timeout=Duration.seconds(300)
        )
        # Configure S3 notifications to SQS
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SqsDestination(self.queue)
        )