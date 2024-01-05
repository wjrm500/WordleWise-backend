# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the necessary files and directories to the working directory
COPY main.py requirements.txt /app/
COPY database /app/database/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define Python path environment variable
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Run main.py when the container launches
CMD ["python", "main.py"]
