# PowerShell script to run the dog breed classifier Docker container

Write-Host "Building and running dog breed classifier..." -ForegroundColor Green

# Build the Docker image
docker build -t dog-breed-classifier .

# Run the container
docker run --rm -it `
  -v "${PWD}/dog_pictures:/app/dog_pictures:ro" `
  -v "${PWD}/model:/app/model:ro" `
  -v "${PWD}/labels.csv:/app/labels.csv:ro" `
  -p 8000:8000 `
  dog-breed-classifier

Write-Host "Container stopped." -ForegroundColor Yellow
