from setuptools import find_packages, setup

with open("deploy-requirements.txt") as stream:
    REQUIREMENTS = stream.read().splitlines()

setup(
    name="cdk_step_function",
    version="0.0.1",
    description="A simple StepFunction created with AWS CDK for Python",
    packages=find_packages(),
    package_dir={"cdk_deployment": "cdk_deployment"},
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
)
