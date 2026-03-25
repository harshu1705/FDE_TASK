# Setup PostgreSQL in Docker
docker rm -f fde_postgres 2>$null
docker run --name fde_postgres -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 postgres:15

Write-Host "Waiting for PostgreSQL to start..."
Start-Sleep -Seconds 5

Write-Host "Copying schema..."
docker cp schema.sql fde_postgres:/schema.sql

Write-Host "Applying schema..."
docker exec fde_postgres psql -U postgres -d postgres -f /schema.sql

Write-Host "Testing database..."
docker exec fde_postgres psql -U postgres -d postgres -c "SELECT * FROM orders;"
