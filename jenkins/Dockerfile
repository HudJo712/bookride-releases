FROM jenkins/jenkins:lts

USER root

# Create docker group with GID 989 and add jenkins user to it
RUN groupadd -for -g 989 docker && usermod -aG docker jenkins

# Install dependencies (python3, pip, docker.io), clean up afterwards
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv docker.io && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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