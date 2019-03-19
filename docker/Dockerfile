FROM python:3-slim

ENV WORLDSIZE=5
ENV NBOBJECTS=10
ENV QUESTLENGTH=5
ENV SEED=1234

RUN apt update && \
  apt install -y build-essential libffi-dev python3-dev curl git && \
  pip install textworld

ADD startup.sh /
CMD ["/bin/sh", "startup.sh"]
