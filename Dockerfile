############################################################
# Dockerfile to build logfile-notifications container images
# Based on python
############################################################
FROM python:3-alpine

# File Author / Maintainer
MAINTAINER ttobias

COPY . script
RUN pip install -r script/requirements.txt

ENTRYPOINT ['python', '/script/notifications.py']
CMD ['script/config.yaml']
