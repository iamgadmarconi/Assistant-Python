# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies for Pillow and other common build needs
RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev libfreetype6-dev \
    libpng-dev libtiff5-dev libjpeg62-turbo-dev libopenjp2-7-dev \
    libwebp-dev libfreetype6-dev liblcms2-dev libtiff5-dev tk-dev tcl-dev \
    libxml2-dev libxslt1-dev libharfbuzz-dev libfribidi-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install Pillow && \
    pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run main.py when the container launches
CMD ["python", "main.py"]
