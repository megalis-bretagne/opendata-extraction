# set base image (host OS)
FROM python:3.11.5-alpine

WORKDIR /appli

COPY requirements.txt .
RUN apk add --no-cache build-base \
  && pip install -r requirements.txt \
  && apk del --no-cache build-base

#COPY uwsgi/ ./uwsgi/
COPY plans-de-comptes/ ./plans-de-comptes/
COPY app/ ./app/
COPY manage.py ./

EXPOSE 80

CMD ["waitress-serve", "--threads=4", "--port=80", "app.api_app.api_serve:app"]