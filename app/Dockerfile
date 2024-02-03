FROM python:3.10

ENV PYTHONUNBUFFERED 1

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install django-storages boto3

EXPOSE 8000

RUN python3 manage.py makemigrations
RUN python3 manage.py migrate

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
