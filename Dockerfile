FROM python:3.9-buster

RUN apt-get update && apt-get install sqlite3 && apt-get clean

WORKDIR /discord-loc

COPY requirements.txt /discord-loc/
RUN pip install -r requirements.txt

COPY *.py /discord-loc/
COPY ./migrations/ /discord-loc/migrations/
CMD python main.py
