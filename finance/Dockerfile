# Use official Python image
FROM python:3.13.2-slim AS base

# Set work directory
WORKDIR /finance

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the application port
EXPOSE 8077

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8077", "--insecure"]
