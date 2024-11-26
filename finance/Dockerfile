# Pull official base image
FROM python:3.7.4

# Set work directory
WORKDIR /finance

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8072

# Install dependencies
COPY ./requirements.txt /finance/requirements.txt
RUN pip install -r requirements.txt

# Copy project files
COPY . /finance/

# Install and run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8072", "--insecure"]
