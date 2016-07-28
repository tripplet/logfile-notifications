############################################################
# Dockerfile to build logfile-notifications container images
# Based on python
############################################################
FROM python

# File Author / Maintainer
MAINTAINER TopCat_TC

RUN apt-get update
RUN pip install --upgrade pip
COPY . script
RUN pip install -r script/requirements.txt

ENTRYPOINT ['python', '/script/notifications.py']
