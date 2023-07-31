ARG OPENNMT_PY_RELEASE=3.1.2

# FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-devel
FROM python:3.10-slim

ARG OPENNMT_PY_RELEASE
ENV PATH="/OpenNMT/onmt/bin":${PATH}

WORKDIR /app


RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get -yqq install \
        git \
        wget \
        gcc \
        g++ \
        libprotobuf-dev \
        protobuf-compiler

# OpenNMT-py
RUN mkdir /OpenNMT && cd /OpenNMT && \
    wget -qO- https://github.com/Redbeard-himalaya/OpenNMT-py/archive/refs/tags/v${OPENNMT_PY_RELEASE}.tar.gz | tar zx -C ./ --strip-components=1 && \
    pip install -e . && \
    pip install sentencepiece
