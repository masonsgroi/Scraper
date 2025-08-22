# Makefile for Dog Breed Classifier Docker operations

.PHONY: help build run test clean logs shell jupyter

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build the Docker image"
	@echo "  run       - Run the container with test script"
	@echo "  test      - Run the test script in container"
	@echo "  model     - Run the model interface in container"
	@echo "  shell     - Start an interactive shell in container"
	@echo "  jupyter   - Start Jupyter Lab"
	@echo "  logs      - Show container logs"
	@echo "  clean     - Remove containers and images"
	@echo "  stop      - Stop all containers"

# Build the Docker image
build:
	docker build -t dog-breed-classifier .

# Run the container with test script
run: build
	docker run --rm -it \
		-v "$(PWD)/dog_pictures:/app/dog_pictures:ro" \
		-v "$(PWD)/model:/app/model:ro" \
		-v "$(PWD)/labels.csv:/app/labels.csv:ro" \
		-p 8000:8000 \
		dog-breed-classifier

# Run the test script
test: build
	docker run --rm -it \
		-v "$(PWD)/dog_pictures:/app/dog_pictures:ro" \
		-v "$(PWD)/model:/app/model:ro" \
		-v "$(PWD)/labels.csv:/app/labels.csv:ro" \
		dog-breed-classifier python test_docker.py

# Run the model interface
model: build
	docker run --rm -it \
		-v "$(PWD)/dog_pictures:/app/dog_pictures:ro" \
		-v "$(PWD)/model:/app/model:ro" \
		-v "$(PWD)/labels.csv:/app/labels.csv:ro" \
		dog-breed-classifier python model_interface.py

# Start an interactive shell
shell: build
	docker run --rm -it \
		-v "$(PWD)/dog_pictures:/app/dog_pictures:ro" \
		-v "$(PWD)/model:/app/model:ro" \
		-v "$(PWD)/labels.csv:/app/labels.csv:ro" \
		dog-breed-classifier /bin/bash

# Start Jupyter Lab
jupyter: build
	docker run --rm -it \
		-v "$(PWD)/dog_pictures:/app/dog_pictures:ro" \
		-v "$(PWD)/model:/app/model:ro" \
		-v "$(PWD)/labels.csv:/app/labels.csv:ro" \
		-v "$(PWD)/notebooks:/app/notebooks" \
		-p 8888:8888 \
		dog-breed-classifier jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''

# Show container logs
logs:
	docker logs dog-breed-classifier

# Stop all containers
stop:
	docker-compose down

# Clean up containers and images
clean:
	docker-compose down
	docker rmi dog-breed-classifier || true
	docker system prune -f
