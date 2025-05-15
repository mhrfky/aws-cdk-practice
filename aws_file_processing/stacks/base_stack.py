from aws_cdk import Stack
from constructs import Construct


class BaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # This is an empty stack that we'll use as a template
        pass