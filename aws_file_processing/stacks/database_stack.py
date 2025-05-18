from aws_cdk import (
    Stack,
    aws_timestream as timestream,
    aws_ec2 as ec2,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define database and table names as class properties
        self.database_name = "file_metrics_db"
        self.events_table_name = "file_events"
        self.file_types_table_name = "file_types"

        # Create Timestream database
        self.timestream_db = timestream.CfnDatabase(self, "FileMetricsDatabase",
                                                    database_name=self.database_name
                                                    )

        # Create a table for file events
        self.events_table = timestream.CfnTable(self, "FileEventsTable",
                                                database_name=self.database_name,
                                                table_name=self.events_table_name,
                                                retention_properties={
                                                    "MemoryStoreRetentionPeriodInHours": "24",
                                                    "MagneticStoreRetentionPeriodInDays": "7"
                                                }
                                                )

        # Create a table for file types
        self.file_types_table = timestream.CfnTable(self, "FileTypesTable",
                                                    database_name=self.database_name,
                                                    table_name=self.file_types_table_name,
                                                    retention_properties={
                                                        "MemoryStoreRetentionPeriodInHours": "24",
                                                        "MagneticStoreRetentionPeriodInDays": "7"
                                                    }
                                                    )

        # Add dependencies
        self.events_table.add_dependency(self.timestream_db)
        self.file_types_table.add_dependency(self.timestream_db)