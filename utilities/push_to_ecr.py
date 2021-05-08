import argparse
import base64
import json
import os
import sys
from pathlib import Path

import boto3
import docker

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ECR_CLIENT = boto3.client("ecr", "eu-west-1")


def main():

    """
    Push an image to ECR

    See: https://github.com/AlexIoannides/py-docker-aws-example-project
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--branch", type=str, help="branch name", required=True)
    parser.add_argument(
        "-er", "--ecrrepository", type=str, help="aws ecr repo name", required=True
    )
    args = parser.parse_args()
    branch = str(args.branch)
    ecrrepository = str(args.ecrrepository)

    print(f"Pushing branch {branch} to repo {ecrrepository}")
    continue_flag = input("Do you want to continue (y/n)?")
    if continue_flag == "y":

        # reset authentication in config file to take care of the known bug
        # where existing stale creds cause login to fail
        # https://github.com/docker/docker-py/issues/2256
        config = Path(Path.home() / ".docker" / "config.json")
        try:
            original = config.read_text()
        except Exception:
            original = None
        try:
            # build Docker image
            docker_client = docker.from_env()
            image_tag = f"{ecrrepository}:{branch}"
            image, build_log = docker_client.images.build(
                path=os.path.join(CURRENT_DIR, "../source"),
                tag=image_tag,
                rm=True,
            )

            # get aws tokens
            token = ECR_CLIENT.get_authorization_token()
            ecr_username, ecr_password = (
                base64.b64decode(token["authorizationData"][0]["authorizationToken"])
                .decode()
                .split(":")
            )
            ecr_url = token["authorizationData"][0]["proxyEndpoint"]
            ecr_registry = ecr_url.replace("https://", "")

            # reset authentication in config file to take care of the known bug
            # where existing stale creds cause login to fail
            # https://github.com/docker/docker-py/issues/2256
            as_json = json.loads(original)
            as_json.pop("auths", None)
            as_json.pop("credsStore", None)
            config.write_text(json.dumps(as_json))

            # get Docker to login/authenticate with ECR
            docker_client.login(
                username=ecr_username, password=ecr_password, registry=ecr_registry
            )
            # tag image for AWS ECR
            ecr_repo_name = "{}/{}".format(ecr_registry, image_tag)
            image.tag(ecr_repo_name, tag=branch)

            # push image to AWS ECR
            for line in docker_client.images.push(
                ecr_repo_name, tag=branch, stream=True, decode=True
            ):
                print(line)

            print("Built and pushed")
        finally:
            if original:
                config.write_text(original)

    else:
        print("Aborted")

    sys.exit(0)


if __name__ == "__main__":

    main()
