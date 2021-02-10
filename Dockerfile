FROM python:3.9-buster

WORKDIR /discord-loc

COPY requirements.txt /discord-loc/
RUN pip install -r requirements.txt

COPY *.py /discord-loc/
CMD python main.py
