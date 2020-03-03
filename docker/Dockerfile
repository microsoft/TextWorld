FROM python:3-slim

# Get everything up-to-date
RUN apt-get update
RUN apt-get upgrade -qy

# Install system dependencies
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

RUN pip install jupyter

RUN git clone --single-branch --branch stable https://github.com/microsoft/TextWorld.git /TextWorld
RUN pip install -r /TextWorld/requirements-full.txt
RUN pip install /TextWorld[vis]

# Environment variables
ENV DISPLAY=:99

CMD ["jupyter", "notebook", "/TextWorld/notebooks", "--ip", "0.0.0.0", "--allow-root"]
