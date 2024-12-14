FROM python:3.12

EXPOSE 5000

RUN pip freeze > requirements.txt
RUN pip install Flask gunicorn
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY src/ app/
WORKDIR /app

ENV PORT 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app