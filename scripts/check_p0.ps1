$ErrorActionPreference = "Stop"

Write-Host "Checking backend Python syntax..."
python -m compileall backend\app

Write-Host "Checking frontend package metadata..."
node -e "JSON.parse(require('fs').readFileSync('frontend/package.json', 'utf8')); console.log('frontend/package.json ok')"

Write-Host "Checking compose files..."
docker compose -f deploy/docker-compose.dev.yml config | Out-Null
docker compose -f deploy/docker-compose.linux.yml config | Out-Null

Write-Host "P0 static checks passed."
