FROM python:3.11
RUN apt update

WORKDIR /monitortelegrambot
COPY ./bot/requirements.txt ./requirements.txt

RUN pip3 install -r ./requirements.txt