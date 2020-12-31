ARG BUILD_FROM=alpine
FROM $BUILD_FROM

ENV LANG C.UTF-8
ENV DESTDIR /
ENV PYTHONPATH /etc/somfy_rts/python

VOLUME /data

# Copy data for add-on
COPY run.sh /
RUN chmod a+x /run.sh

# Set work dir
WORKDIR /tmp

# Install dependencies
RUN apk add --update alpine-sdk && apk update
RUN apk add --update gcc && apk update
RUN apk add --no-cache python3

# Install pigpio
RUN \
    wget https://github.com/joan2937/pigpio/archive/master.zip \
    && unzip master.zip \
    && cd pigpio-master \
    && make \
    && make install
RUN rm -rf master.zip && rm -rf pigpio-master

# Install Python
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Install Somfy RTS
RUN mkdir -p /etc/somfy_rts/python
COPY python /etc/somfy_rts/python/


WORKDIR /
CMD [ "/run.sh" ]
