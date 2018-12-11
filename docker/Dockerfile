FROM debian:buster

MAINTAINER TextWorld Team <textworld@microsoft.com>

# Get everything up-to-date
RUN apt-get update
RUN apt-get upgrade -qy

RUN apt-get install -qy \
    build-essential \
    chromium \
    chromium-driver \
    curl \
    git \
    libffi-dev \
    python3-dev \
    python3-pip \
    wget \
    graphviz

# set display name for x-server for selenium tests
ENV DISPLAY=:99