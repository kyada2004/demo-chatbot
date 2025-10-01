#!/bin/bash

# Build and run the docker containers
docker-compose up -d --build

# You can add other deployment steps here, like database migrations

# Show the logs
docker-compose logs -f
