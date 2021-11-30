# set base image (host OS)
FROM python:3.9.5-slim-buster

RUN apt-get update
RUN apt-get install -y xmlstarlet

# set the working directory in the container
WORKDIR /appli

COPY requirements.txt .
RUN pip install -r requirements.txt

#COPY uwsgi/ ./uwsgi/
COPY tests/ ./tests/
COPY shared/ ./shared/
RUN chmod u+x /appli/shared/totem/totem2csv/totem2csv.sh
COPY app/ ./app/
COPY manage.py ./

EXPOSE 80

#ENTRYPOINT ["python", "/appli/manage.py", "runserver"," -h 0.0.0.0", "-p 80"]
CMD ["python", "/appli/manage.py", "runserver","-h", "0.0.0.0","-p","80"]
#CMD [ "python", "/appli/manage.py runserver -h 0.0.0.0 -p 80" ]
