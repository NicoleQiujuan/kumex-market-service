FROM python:latest

RUN pip install python-kumex
COPY ./ /usr/src/app/
WORKDIR /usr/src/app
CMD ["./trade.py"]