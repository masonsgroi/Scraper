# Dog Breed Classification Project

A machine learning project for identifying dog breeds from images using TensorFlow/Keras.

## Project Structure

```
sf_coding_class_project/
├── model_interface.py      # Main classification script
├── labels.csv             # Dog breed labels
├── dog_pictures/          # Test images organized by breed
├── public/                # Web interface files
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── scripts/               # Helper scripts
└── README.md             # This file
```

## Quick Start with Docker

### Prerequisites

- Docker installed on your system
- Docker Compose (usually comes with Docker Desktop)

### Option 1: Using Docker Compose (Recommended)

1. **Build and run the main service:**
   ```bash
   docker compose up dog-breed-classifier
   ```

2. **Run with Jupyter Lab for development:**
   ```bash
   docker compose up jupyter
   ```
   Then open http://localhost:8888 in your browser.

3. **Run all services:**
   ```bash
   docker compose up
   ```

### Option 2: Using Docker directly

**On Linux/Mac:**
```bash
chmod +x scripts/run_docker.sh
./scripts/run_docker.sh
```

**On Windows (PowerShell):**
```powershell
.\scripts\run_docker.ps1
```

**Manual Docker commands:**
```bash
# Build the image
docker build -t dog-breed-classifier .

# Run the container and execute model_interface.py
docker run --rm -it -v "$(pwd)":/app dog-breed-classifier python model_interface.py

## Development Setup

### Local Python Environment

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the model:**
   ```bash
   python model_interface.py
   ```

## Model Requirements

The project expects:
- A trained model in the `./model/` directory
- A `labels.csv` file with breed labels
- Test images in the `dog_pictures/` directory

## Features

- **Consistent Environment**: Docker ensures the same environment across different machines
- **Virtual Environment**: Python virtual environment isolated within the container
- **Volume Mounting**: Easy access to local files without copying them into the container
- **Development Tools**: Optional Jupyter Lab for interactive development
- **Cross-Platform**: Works on Windows, Mac, and Linux

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure you have a trained model in the `./model/` directory
2. **Permission errors**: Make sure Docker has access to your project directory
3. **Port conflicts**: Change the port mapping in docker-compose.yml if port 8000 is in use

### Docker Commands

```bash
# View running containers
docker ps

# View logs
docker logs dog-breed-classifier

# Stop all containers
docker compose down

# Remove all images
docker system prune -a
```

## Contributing

1. Make changes to your code
2. Rebuild the Docker image: `docker-compose build`
3. Test your changes: `docker-compose up`

