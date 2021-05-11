# pull official base image
FROM python:3.7.4

# set work directory
WORKDIR /finance

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# install dependencies
COPY ./requirements.txt /finance/requirements.txt
RUN pip install -r requirements.txt


# copy project
COPY . /finance/