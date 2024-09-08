FROM python:alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ../djangoTemplate%20copy /app/

EXPOSE 5000

CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]

