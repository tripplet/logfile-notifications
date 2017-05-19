############################################################
# Dockerfile to build logfile-notifications container images
# Based on python
############################################################
FROM python:3-alpine

# File Author / Maintainer
MAINTAINER ttobias

# Copy script into container
COPY . script
 
RUN apk add --update ca-certificates && \
    apk add tzdata && \
    apk add git --virtual .build-deps git && \
    pip install -r script/requirements.txt && \
    cd /script/ && git describe --long --always --tags > /script/.version && \
    apk del .build-deps && rm -rf /script/.git

ENTRYPOINT ["python", "/script/notifications.py"]
CMD ["config.yaml"]

