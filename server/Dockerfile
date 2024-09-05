FROM python:alpine

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir flask
RUN pip install --no-cache-dir requests

EXPOSE 5000

CMD ["python", "app.py"]
