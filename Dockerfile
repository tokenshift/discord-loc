FROM python:3.9-buster

WORKDIR /discord-loc

COPY *.py /discord-loc/
COPY requirements.txt /discord-loc/

RUN pip install -r requirements.txt
CMD python main.py
