# Step Function deployment with CDK - utilities

A collection of files useful for the deployment. Before running, install requirements.

```
pip install -r ecr-requirements.txt
```


## Push the docker image into the ECR

To push the docker image built with the Dockerfile inside `source`, run the following:

```
python push_to_ecr.py --branch <branch_name> --ecrrepository <ecr repo name>
```

In the command above `<ecr repo name>` should be the repo where the image is going to be pushed and `<branch_name>` the name of the branch to push, which will be used as tag.


## Delete the docker image from the ECR

To delete a docker image for branch `<branch_name>` from the ecr repository `<ecr repo name>`, run the following:

```
python delete_from_ecr.py --branch <branch_name> --ecrrepository <ecr repo name>
```