#!/bin/bash

# Script to run the dog breed classifier Docker container

echo "Building and running dog breed classifier..."

# Build the Docker image
docker build -t dog-breed-classifier .

# Run the container
docker run --rm -it \
  -v "$(pwd)/dog_pictures:/app/dog_pictures:ro" \
  -v "$(pwd)/model:/app/model:ro" \
  -v "$(pwd)/labels.csv:/app/labels.csv:ro" \
  -p 8000:8000 \
  dog-breed-classifier

echo "Container stopped."
