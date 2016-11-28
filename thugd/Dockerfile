# Distributed Thug (thugd) Dockerfile for Ubuntu 16.04 (Xenial)
#   based on remnux/thug (https://hub.docker.com/r/remnux/thug)

FROM ubuntu:16.04

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    build-essential \
    git \
    graphviz \
    graphviz-dev \
    libboost-all-dev \
    libboost-python-dev \
    libffi-dev \
    libfuzzy-dev \
    libgraphviz-dev \
    libjpeg8-dev \
    libtool \
    libxml2-dev \
    libxslt-dev \
    python-dev \
    python-pip \
    python3 \
    python3-pip \
    python3-requests \
    python-pygraphviz \
    python-setuptools \
    ssdeep && \
  rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/thug

WORKDIR /home
RUN git clone https://github.com/buffer/pyv8.git && \
  cd pyv8 && \
  python setup.py build && \
  python setup.py install && \
  cd .. && \
  rm -rf pyv8
RUN pip install thug
RUN pip3 install pika

RUN groupadd -r thug && \
  useradd -r -g thug -d /home/thug -s /sbin/nologin -c "Thug user" thug && \
  mkdir -p /home/thug /tmp/thug/logs && \
  chown -R thug:thug /home/thug /tmp/thug/logs

RUN echo "/opt/libemu/lib/" > /etc/ld.so.conf.d/libemu.conf && ldconfig
RUN mkdir -p /data/thug && chown -R thug:thug /data/thug

USER thug
WORKDIR /home/thug
COPY ["thugd.py", "thuglet.py", "thugd.ini", "/home/thug/"]
COPY ["logging.conf", "/etc/thug/"]

VOLUME ["/data/thug"]
CMD ["python3", "/home/thug/thuglet.py", "-c", "thugd.ini"]
