FROM jenkins/jenkins:lts

USER root

# Align docker group GID with host (override via build arg if needed)
ARG DOCKER_GID=989
RUN groupadd -for -g ${DOCKER_GID} docker && usermod -aG docker jenkins

# Install dependencies (python3, pip, curl), clean up afterwards
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv curl && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install recent Docker CLI to satisfy newer daemon API requirements
ARG DOCKER_CLI_VERSION=29.0.0
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz \
    -o /tmp/docker.tgz && \
    tar xz -C /usr/local/bin --strip-components=1 -f /tmp/docker.tgz docker/docker && \
    rm /tmp/docker.tgz

# Install Docker Compose CLI plugin
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -SL https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-linux-x86_64 \
    -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
 && chmod +x kubectl \
 && mv kubectl /usr/local/bin/

# Copy plugins.txt
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

# Use jenkins-plugin-cli instead
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

RUN mkdir -p /var/jenkins_home/.ssh && \
    ssh-keyscan -t ed25519 github.com >> /var/jenkins_home/.ssh/known_hosts


USER jenkins
