FROM python:3.10

ENV PYTHONUNBUFFERED 1

COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000

RUN python3 manage.py makemigrations
RUN python3 manage.py migrate

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
