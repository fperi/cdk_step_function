# Step Function deployment with CDK - deployment

This folder contains a CDK app for the deployment of the step function to AWS.

### Requirements

Install CDK (available on mac with `brew install aws-cdk`), install the requirements:

```
pip install -r deploy-requirements.txt
```

### How to run

Check that the "grammar" is correct:

```
cdk ls -c branch=<branch_name> -c ecr_repository=<ecr_repo_name> -c account=<account> -c region=<region>
```

In the command above `<ecr_repo_name>` should be the ecr repo where the image for branch `<branch_name>` is available. `<account>` should be your aws account id and `<region>` the region where you want to deploy. The reason for passing these through context is that in this way the code does not contain any sensitive information.

Deploy with:

```
cdk deploy all -c branch=<branch_name> -c ecr_repository=<ecr_repo_name> -c account=<account> -c region=<region>
```

At this point the step function should appear in the AWS console. You can
trigger a new execution passing the following json as input.

Destroy with:

```
cdk destroy all -c branch=<branch_name> -c ecr_repository=<ecr_repo_name> -c account=<account> -c region=<region>
```

The entire deployment is orchestrated by the `app.py`, which imports the stacks and consequently creates all the necessary roles, policies and resources. The code filled with inline comments to better understand the logic of the deployment.