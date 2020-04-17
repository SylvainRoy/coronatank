FROM python:3.7
MAINTAINER Sylvain Roy "sylvain.roy@m4x.org"
ENV REFRESHED_AT 17Apr20

RUN mkdir /var/tank
ADD . /var/tank

RUN pip install pygame

WORKDIR /var/tank
CMD python /var/tank/server.py --listen 0.0.0.0:8888

EXPOSE 8888
