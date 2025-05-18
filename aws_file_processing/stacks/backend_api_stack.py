# aws_file_processing/stacks/backend_api_stack.py
from aws_cdk import (
    NestedStack,
    RemovalPolicy,
    CfnOutput,  # Add CfnOutput import
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
)
from constructs import Construct


class BackendApiStack(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 vpc, timestream_db_name, timestream_events_table_name,
                 timestream_file_types_table_name, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Remove the env parameter from kwargs since NestedStack doesn't use it
        if 'env' in kwargs:
            del kwargs['env']

        # Create ECR Repository for API
        self.repository = ecr.Repository(self, "ApiRepository",
                                         repository_name="file-processing-api",
                                         removal_policy=RemovalPolicy.DESTROY
                                         )

        # Create task role with Timestream permissions
        task_role = self._create_task_role(timestream_db_name, timestream_events_table_name,
                                           timestream_file_types_table_name)

        # Create Fargate service
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "ApiService",
                                                                                  vpc=vpc,
                                                                                  memory_limit_mib=512,
                                                                                  cpu=256,
                                                                                  desired_count=1,
                                                                                  task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                                                                                      image=ecs.ContainerImage.from_ecr_repository(
                                                                                          self.repository, "latest"),
                                                                                      container_port=5000,
                                                                                      environment={
                                                                                          "TIMESTREAM_DB_NAME": timestream_db_name,
                                                                                          "TIMESTREAM_EVENTS_TABLE": timestream_events_table_name,
                                                                                          "TIMESTREAM_FILE_TYPES_TABLE": timestream_file_types_table_name,
                                                                                          "AWS_REGION": self.region
                                                                                      },
                                                                                      task_role=task_role
                                                                                  ),
                                                                                  public_load_balancer=True
                                                                                  )

        # Configure health check
        self.fargate_service.target_group.configure_health_check(
            path="/api/health",
            healthy_http_codes="200"
        )

        # Add auto-scaling
        scaling = self.fargate_service.service.auto_scale_task_count(
            max_capacity=5,
            min_capacity=1
        )

        scaling.scale_on_cpu_utilization("CpuScaling",
                                         target_utilization_percent=70
                                         )

        # Output the API endpoint URL
        self.api_url = self.fargate_service.load_balancer.load_balancer_dns_name

        # Add outputs for CI/CD integration
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

        CfnOutput(self, "ApiEndpoint",
                  value=self.api_url,
                  description="The endpoint URL of the API",
                  export_name="ApiEndpoint"
                  )

        CfnOutput(self, "ApiRepositoryName",
                  value=self.repository.repository_name,
                  description="The name of the ECR repository",
                  export_name="ApiRepositoryName"
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