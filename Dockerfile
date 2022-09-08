# set base image (host OS)
FROM python:3.9.13-alpine

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

#ENTRYPOINT ["python", "/appli/manage.py", "runserver"," -h 0.0.0.0", "-p 80"]
#CMD ["python", "/appli/manage.py", "runserver","-h", "0.0.0.0","-p","80"]
#CMD [ "python", "/appli/manage.py runserver -h 0.0.0.0 -p 80" ]
CMD ["waitress-serve","--port=80","--call", "app:create_app"]