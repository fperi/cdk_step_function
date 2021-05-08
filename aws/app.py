from aws_cdk import core
from cdk_deployment.main_stack import MainStack

# start cdk
app = core.App()

# retrieve the name of the branch and the ecr repo to pull from
ecr_repository_name = app.node.try_get_context("ecr_repository")
branch_name = app.node.try_get_context("branch")
account = app.node.try_get_context("account")
region = app.node.try_get_context("region")
if not branch_name or not ecr_repository_name or not account or not region:
    raise Exception("Branch, ECR repository, account and region are required")

print(
    f"Working on branch {branch_name} ",
    f"ECR repository {ecr_repository_name} ",
    f"account {account} ",
    f"region {region}",
)

# setup environment, ie account and region where to deploy
env_EU = core.Environment(account=account, region=region)

# create the stack
# csfe stands for CDK step function example
_ = MainStack(
    app,
    "csfeMainStack",
    stack_name=f"csfe-{branch_name}-main-stack",
    env=env_EU,
    ecr_repository_name=ecr_repository_name,
    branch_name=branch_name,
    account=account,
    region=region,
)

# synthesize the app into a cloud assembly, ie an ensamble of artifacts
# such as CloudFormation templates and assets that are needed to deploy
# this app into the AWS cloud.
app.synth()
