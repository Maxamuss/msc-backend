# pull official base image
FROM python:3.9.2-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
    && apt-get install -y libpq-dev python3-dev

# install dependencies
RUN pip install --upgrade pip
RUN python -m pip install --upgrade setuptools
COPY requirements requirements
RUN pip install -r requirements/dev.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["sh", "/usr/src/app/entrypoint.sh"]