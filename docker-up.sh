#!/bin/bash

# Get the Docker group ID on the host system
DOCKER_GID=$(getent group docker | cut -d: -f3)

# Export it as an environment variable for docker-compose
export DOCKER_GROUP_ID=$DOCKER_GID

echo "Setting DOCKER_GROUP_ID=$DOCKER_GID for docker-compose..."

# Run docker-compose with the environment variable
docker-compose up "$@"
