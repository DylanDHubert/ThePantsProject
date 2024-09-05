FROM python:alpine

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir flask

EXPOSE 8000

CMD ["python", "process.py"]