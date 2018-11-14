FROM ubuntu:16.04

COPY build/java_policy /etc

# Mono
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
RUN apt-get update
RUN apt install -y apt-transport-https
RUN "deb https://download.mono-project.com/repo/ubuntu stable-xenial main" | tee /etc/apt/sources.list.d/mono-official-stable.list
# Deps
RUN buildDeps='software-properties-common git libtool cmake python-dev python3-pip python-pip libseccomp-dev' && \
    apt-get update && apt-get install -y python python3.5 python-pkg-resources python3-pkg-resources gcc g++ $buildDeps
RUN add-apt-repository ppa:openjdk-r/ppa && apt-get update && apt-get install -y openjdk-8-jdk
RUN pip3 install --no-cache-dir psutil gunicorn flask requests pika
RUN cd /tmp && git clone -b newnew  --depth 1 https://github.com/ospiper/Judger.git && cd Judger && \ 
    mkdir build && cd build && cmake .. && make && make install && cd ../bindings/Python && python3 setup.py install
# Install Mono
RUN apt install -y mono-complete
# Purge
RUN buildDeps='software-properties-common git libtool cmake python-dev python3-pip python-pip libseccomp-dev' && \
    apt-get purge -y --auto-remove $buildDeps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /code && useradd -r compiler && useradd -r code

# HEALTHCHECK --interval=5s --retries=3 CMD python3 /code/service.py
ADD server /code
WORKDIR /code
EXPOSE 8080
ENTRYPOINT /code/entrypoint.sh
