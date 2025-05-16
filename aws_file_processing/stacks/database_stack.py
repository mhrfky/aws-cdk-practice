from aws_cdk import (
    Stack,
    CfnResource,
    aws_ec2 as ec2,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Timestream database using L1 construct (direct CloudFormation)
        self.timestream_db = CfnResource(self, "FileMetricsDatabase",
                                         type="AWS::Timestream::Database",
                                         properties={
                                             "DatabaseName": "file_metrics_db"
                                         }
                                         )

        # Create a table for file events
        self.events_table = CfnResource(self, "FileEventsTable",
                                        type="AWS::Timestream::Table",
                                        properties={
                                            "DatabaseName": "file_metrics_db",
                                            "TableName": "file_events",
                                            "RetentionProperties": {
                                                "MemoryStoreRetentionPeriodInHours": "24",
                                                "MagneticStoreRetentionPeriodInDays": "7"
                                            }
                                        }
                                        )

        # Create a table for file types
        self.file_types_table = CfnResource(self, "FileTypesTable",
                                            type="AWS::Timestream::Table",
                                            properties={
                                                "DatabaseName": "file_metrics_db",
                                                "TableName": "file_types",
                                                "RetentionProperties": {
                                                    "MemoryStoreRetentionPeriodInHours": "24",
                                                    "MagneticStoreRetentionPeriodInDays": "7"
                                                }
                                            }
                                            )

        # Add dependencies
        self.events_table.add_depends_on(self.timestream_db)
        self.file_types_table.add_depends_on(self.timestream_db)

        # Store names for access in other stacks
        self.database_name = "file_metrics_db"
        self.events_table_name = "file_events"
        self.file_types_table_name = "file_types"