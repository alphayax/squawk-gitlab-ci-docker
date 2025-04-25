FROM debian:bookworm-slim

ADD json2glnote.py /json2glnote.py

RUN apt-get update -qq \
 && apt-get install -qqy wget git python3 python3-requests \
 && apt-get clean

RUN wget -nv https://github.com/sbdchd/squawk/releases/download/v1.6.0/squawk-linux-x64 \
 && install squawk-linux-x64 /usr/local/bin/squawk \
 && rm squawk-linux-x64
