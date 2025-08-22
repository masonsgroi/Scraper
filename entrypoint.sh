#!/bin/bash

# Entrypoint script for the dog breed classifier Docker container

set -e

echo "Dog Breed Classifier Container Starting..."
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

# Check if a specific command was passed
if [ $# -eq 0 ]; then
    echo "No command specified, running test script..."
    exec python test_docker.py
else
    echo "Running command: $@"
    exec "$@"
fi
