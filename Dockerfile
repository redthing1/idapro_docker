FROM debian:bookworm-slim

ARG IDA_DIR
ARG IDA_LICENSE

# update system and install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates python3 python3-pip \
        libssl3 libffi8 libc6 libstdc++6 && \
    # cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install uv globally
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/ && \
    mv /root/.local/bin/uvx /usr/local/bin/

# copy ida directory
COPY ${IDA_DIR} /opt/idapro
# validate that it contains ida binary
RUN test -f /opt/idapro/ida || test -f /opt/idapro/ida64 || test -f /opt/idapro/idat || test -f /opt/idapro/idat64

# set environment variables
ENV IDADIR=/opt/idapro
ENV PATH="/opt/idapro:${PATH}"

# create an unprivileged user
RUN useradd -m -d /home/user -s /bin/bash user && \
    mkdir -p /home/user/.idapro && \
    chown -R user:user /home/user

# set Tini as entrypoint for signal handling
ENV TINI_VERSION=v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# copy license file to correct location
COPY ${IDA_LICENSE} /home/user/.idapro/idapro.hexlic

# copy ida domain server script
COPY ida_domain_server.py /home/user/ida_domain_server.py
RUN chmod +x /home/user/ida_domain_server.py && chown user:user /home/user/ida_domain_server.py /home/user/.idapro/idapro.hexlic

ENTRYPOINT ["/tini", "--"]

USER user

# expose rpyc server port
EXPOSE 18812

# run ida domain server
CMD ["/home/user/ida_domain_server.py", "--host", "0.0.0.0", "--port", "18812"]