import argparse
import sys

import boto3

ECR_CLIENT = boto3.client("ecr", "eu-west-1")


def main():

    """
    Delete an image from ECR
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--branch", type=str, help="branch name", required=True)
    parser.add_argument(
        "-er", "--ecrrepository", type=str, help="aws ecr repo name", required=True
    )
    args = parser.parse_args()
    branch = str(args.branch)
    ecrrepository = str(args.ecrrepository)

    print(f"Deleting branch {branch} from repo {ecrrepository}")
    continue_flag = input("Do you want to continue (y/n)?")
    if continue_flag == "y":
        ECR_CLIENT.batch_delete_image(
            repositoryName=ecrrepository, imageIds=[{"imageTag": branch}]
        )
        print(f"Deleted")
    else:
        print(f"Aborted")

    sys.exit(0)


if __name__ == "__main__":

    main()
