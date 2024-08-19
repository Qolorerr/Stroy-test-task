# Simple FastAPI project for Stroy otdelka
This project provides an API for managing items on trading platform

## Project Overview
The Item API allows creating, updating, and deleting items

## Installation
1. Install Docker on your system
2. Clone this repository: `git clone https://github.com/Qolorerr/Stroy-test-task.git item_api`
3. Build the Docker image: `docker build -t item-api .`
4. Run the Docker container: `docker run -p 8000:8000 item-api`
The API will now be available on port 8000 of your Docker host.

## Configuration
The database file is defined using the DB_PATH environment variable inside the Docker container.

## Usage
You can now make requests to the API running inside the Docker container on port 8000.

## API Documentation
Documentation can be seen on `<your-server-ip>:8000/docs` or on `<your-server-ip>:8000/redoc`
