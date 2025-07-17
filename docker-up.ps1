# PowerShell script to set Docker group ID and run docker-compose

# For Windows, we typically use a default group ID since Windows doesn't use the same group mechanism
$env:DOCKER_GROUP_ID = 999

Write-Host "Setting DOCKER_GROUP_ID=$env:DOCKER_GROUP_ID for docker-compose..."

# Run docker-compose with the environment variable
docker-compose up $args
