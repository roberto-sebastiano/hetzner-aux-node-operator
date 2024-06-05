From phusion/baseimage:jammy-1.0.4


ARG DEBIAN_FRONTEND=noninteractive
# update the following to force apt-get update
LABEL package.date=2025-06-09


RUN apt-get update && apt-get install -y curl
RUN apt-get install -y python3-pip iputils-ping curl nano net-tools locales locales-all psmisc

COPY code /opt/code
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

CMD ["sh", "-c", "sleep infinity"]
