from setuptools import find_packages, setup

with open("requirements.txt") as stream:
    REQUIREMENTS = stream.read().splitlines()

setup(
    name="cdk_test",
    version="1.0",
    description="Test app for cdk deployment",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
    zip_safe=False,
)
