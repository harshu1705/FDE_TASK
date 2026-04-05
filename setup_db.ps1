# Setup PostgreSQL in Docker
$containerName = 'fde_postgres'
$existing = docker ps -a --filter "name=$containerName" --format "{{.Names}}"
if ($existing -eq $containerName) {
    Write-Host "Container $containerName already exists. Starting if stopped..."
    docker start $containerName | Out-Null
} else {
    Write-Host "Creating container $containerName..."
    docker run --name $containerName -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 postgres:15
}

Write-Host "Waiting for PostgreSQL to start..."
Start-Sleep -Seconds 5

Write-Host "Copying schema..."
docker cp schema.sql $containerName:/schema.sql

Write-Host "Applying schema..."
docker exec $containerName psql -U postgres -d postgres -f /schema.sql

Write-Host "Testing database..."
docker exec $containerName psql -U postgres -d postgres -c "SELECT * FROM orders;"
