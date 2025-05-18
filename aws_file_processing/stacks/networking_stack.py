from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct

class NetworkingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC with public and private subnets
        self.vpc = ec2.Vpc(self, "FileProcessingVpc",
                           max_azs=2,  # Use 2 Availability Zones
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   name="Public",
                                   subnet_type=ec2.SubnetType.PUBLIC,
                                   cidr_mask=24
                               ),
                               ec2.SubnetConfiguration(
                                   name="Private",
                                   subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                                   cidr_mask=24
                               )
                           ],
                           nat_gateways=1  # For cost optimization, use only one NAT gateway
                           )

        # Create Security Group for Lambda functions
        self.lambda_sg = ec2.SecurityGroup(self, "LambdaSecurityGroup",
                                           vpc=self.vpc,
                                           description="Security group for Lambda functions",
                                           allow_all_outbound=True
                                           )

        # Create Security Group for databases/cache
        self.data_sg = ec2.SecurityGroup(self, "DatabaseSecurityGroup",
                                         vpc=self.vpc,
                                         description="Security group for database resources",
                                         allow_all_outbound=True
                                         )

        # Allow Lambda to access database resources
        self.data_sg.add_ingress_rule(
            peer=self.lambda_sg,
            connection=ec2.Port.tcp(6379),  # Redis port
            description="Allow Lambda functions to connect to Redis"
        )