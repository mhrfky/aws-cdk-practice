from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
)
from constructs import Construct


class BackendApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 vpc, timestream_db_name, timestream_events_table_name,
                 timestream_file_types_table_name, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create ECR Repository for API
        self.repository = ecr.Repository(self, "ApiRepository",
                                         repository_name="file-processing-api",
                                         removal_policy=RemovalPolicy.DESTROY
                                         )

        # Create IAM task role with permissions
        task_role = self._create_task_role(timestream_db_name, timestream_events_table_name,
                                           timestream_file_types_table_name)

        # Create a Task Definition with a name we can reference
        self.task_definition = ecs.FargateTaskDefinition(self, "ApiTaskDefinition",
                                                         memory_limit_mib=512,
                                                         cpu=256,
                                                         task_role=task_role
                                                         )

        # Add container to the task definition with placeholder image
        container = self.task_definition.add_container("ApiContainer",
                                                       # Use placeholder image initially
                                                       image=ecs.ContainerImage.from_registry(
                                                           "amazon/amazon-ecs-sample"),
                                                       environment={
                                                           "TIMESTREAM_DB_NAME": timestream_db_name,
                                                           "TIMESTREAM_EVENTS_TABLE": timestream_events_table_name,
                                                           "TIMESTREAM_FILE_TYPES_TABLE": timestream_file_types_table_name,
                                                           "AWS_REGION": self.region
                                                       },
                                                       logging=ecs.LogDrivers.aws_logs(stream_prefix="api-container")
                                                       )

        # Add port mapping
        container.add_port_mappings(ecs.PortMapping(container_port=80))

        # Create Fargate Service with this task definition
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "ApiService",
                                                                                  vpc=vpc,
                                                                                  task_definition=self.task_definition,
                                                                                  desired_count=1,
                                                                                  public_load_balancer=True
                                                                                  )

        # Configure health check for placeholder image
        self.fargate_service.target_group.configure_health_check(
            path="/",  # The sample image serves content at root
            healthy_http_codes="200"
        )

        # Add auto-scaling
        scaling = self.fargate_service.service.auto_scale_task_count(
            max_capacity=3,
            min_capacity=1
        )

        scaling.scale_on_cpu_utilization("CpuScaling",
                                         target_utilization_percent=70
                                         )

        # Output values needed for CI/CD
        CfnOutput(self, "ApiRepositoryName",
                  value=self.repository.repository_name,
                  description="The name of the ECR repository",
                  export_name="ApiRepositoryName"
                  )

        CfnOutput(self, "ApiClusterName",
                  value=self.fargate_service.cluster.cluster_name,
                  description="The name of the ECS cluster",
                  export_name="ApiClusterName"
                  )

        CfnOutput(self, "ApiServiceName",
                  value=self.fargate_service.service.service_name,
                  description="The name of the ECS service",
                  export_name="ApiServiceName"
                  )

        CfnOutput(self, "ApiTaskDefinitionFamily",
                  value=self.task_definition.family,
                  description="The family name of the task definition",
                  export_name="ApiTaskDefinitionFamily"
                  )

        CfnOutput(self, "ApiEndpoint",
                  value=self.fargate_service.load_balancer.load_balancer_dns_name,
                  description="The endpoint URL of the API",
                  export_name="ApiEndpoint"
                  )

    def _create_task_role(self, timestream_db_name, timestream_events_table_name, timestream_file_types_table_name):
        task_role = iam.Role(self, "ApiTaskRole",
                             assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
                             )

        # Add Timestream read permissions
        region = self.region
        account = self.account

        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "timestream:Select",
                    "timestream:DescribeTable",
                    "timestream:DescribeDatabase",
                    "timestream:ListMeasures"
                ],
                resources=[
                    f"arn:aws:timestream:{region}:{account}:database/{timestream_db_name}",
                    f"arn:aws:timestream:{region}:{account}:database/{timestream_db_name}/table/{timestream_events_table_name}",
                    f"arn:aws:timestream:{region}:{account}:database/{timestream_db_name}/table/{timestream_file_types_table_name}"
                ]
            )
        )

        return task_role