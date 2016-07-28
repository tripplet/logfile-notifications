############################################################
# Dockerfile to build logfile-notifications container images
# Based on python
############################################################
FROM python:3-alpine

# File Author / Maintainer
MAINTAINER ttobias

# Certificates for SSL
RUN apk add --update ca-certificates

# Copy script into container and install requirements
COPY . script
RUN pip install -r script/requirements.txt

# Save version
RUN cat /script/.git/refs/heads/master > /script/.version

ENTRYPOINT ["python", "/script/notifications.py"]
CMD ["config.yaml"]
