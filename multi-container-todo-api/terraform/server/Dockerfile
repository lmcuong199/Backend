# The definition of your simulated server
# - A bare Ubuntu machine with SSH and nothing else (there's no Docker in it)

FROM ubuntu:24.04

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      openssh-server sudo python3 ca-certificates curl gnupg \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd /root/.ssh \
 && chmod 700 /root/.ssh \
 && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D", "-e"]
