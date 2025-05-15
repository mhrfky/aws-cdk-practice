from aws_cdk import (
    Stack,
    aws_timestream as timestream,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Timestream database
        self.timestream_db = timestream.CfnDatabase(self, "FileMetricsDatabase",
                                                    database_name="file_metrics_db"
                                                    )

        # Create a table for file processing events
        self.events_table = timestream.CfnTable(self, "FileEventsTable",
                                                database_name=self.timestream_db.database_name,
                                                table_name="file_events",
                                                retention_properties={
                                                    "MemoryStoreRetentionPeriodInHours": "24",
                                                    "MagneticStoreRetentionPeriodInDays": "7"
                                                }
                                                )

        # Create a table for file type metrics
        self.file_types_table = timestream.CfnTable(self, "FileTypesTable",
                                                    database_name=self.timestream_db.database_name,
                                                    table_name="file_types",
                                                    retention_properties={
                                                        "MemoryStoreRetentionPeriodInHours": "24",
                                                        "MagneticStoreRetentionPeriodInDays": "7"
                                                    }
                                                    )

        # Make sure tables are created after the database
        self.events_table.add_depends_on(self.timestream_db)
        self.file_types_table.add_depends_on(self.timestream_db)