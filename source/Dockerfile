FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y \
    && apt-get install -y python3 \
    python3-pip \
    && apt-get clean \
    && apt-get autoremove

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

ADD . /home/cdk_test/source
WORKDIR /home/cdk_test/source
RUN pip3 install .

ENV PARAMETER parameter

CMD ["/bin/bash", "-c", "python3 main.py -p ${PARAMETER}"]