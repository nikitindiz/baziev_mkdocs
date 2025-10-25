# Docker Compose Setup with APOC

If you prefer using Docker Compose for easier management, use this configuration.

## Quick Start

```bash
# Start Neo4j with APOC
docker-compose up -d

# View logs
docker-compose logs -f neo4j

# Verify APOC
python verify_apoc.py
```

## Access Neo4j

- **Browser UI**: http://localhost:7474
- **Bolt connection**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: 20021030 (change in docker-compose.yml)

## Configuration

The `docker-compose.yml` file includes:

- ✅ Neo4j 5.14 Community Edition
- ✅ APOC plugin pre-installed
- ✅ Persistent data volumes
- ✅ Health checks
- ✅ Proper memory limits

## Commands

### Start/Stop

```bash
# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Logs and Status

```bash
# View logs
docker-compose logs -f neo4j

# Check status
docker-compose ps

# Check resource usage
docker stats neo4j-baziev
```

### Verify APOC Installation

```bash
# Method 1: Using verify script
python verify_apoc.py

# Method 2: Direct docker exec
docker exec -it neo4j-baziev cypher-shell -u neo4j -p 20021030 \
  "CALL apoc.help('apoc') YIELD name RETURN count(name) as procedures"

# Method 3: Check logs for APOC loading
docker-compose logs neo4j | grep -i apoc
```

Expected output:
```
Successfully loaded APOC
```

## Backup and Restore

### Backup

```bash
# Create backup
docker exec neo4j-baziev neo4j-admin database dump neo4j --to-path=/data/backup
docker cp neo4j-baziev:/data/backup ./neo4j-backup

# Or using export
python main.py export json -o backup.json
```

### Restore

```bash
# From dump
docker cp ./neo4j-backup neo4j-baziev:/data/backup
docker exec neo4j-baziev neo4j-admin database load neo4j --from-path=/data/backup

# Or reimport
python main.py import all
```

## Environment Variables

Update `.env` to match Docker configuration:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=20021030
NEO4J_DATABASE=neo4j
```

## Troubleshooting

### APOC not loading

```bash
# Check plugins directory
docker exec -it neo4j-baziev ls -la /var/lib/neo4j/plugins/

# Check logs
docker-compose logs neo4j | grep -i apoc

# Restart
docker-compose restart neo4j
```

### Connection refused

```bash
# Check container status
docker-compose ps

# Check health
docker-compose exec neo4j wget --spider http://localhost:7474

# View recent logs
docker-compose logs --tail=100 neo4j
```

### Out of memory

Edit `docker-compose.yml`:
```yaml
- NEO4J_server_memory_heap_max__size=4G
- NEO4J_server_memory_pagecache_size=1G
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## Switching from Local to Docker

1. **Export existing data**:
   ```bash
   python main.py export json -o backup.json
   ```

2. **Start Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Wait for Neo4j to start** (check logs):
   ```bash
   docker-compose logs -f neo4j
   ```

4. **Import data**:
   ```bash
   python main.py import all
   ```

## Production Considerations

### Use Secrets for Passwords

Create `secrets/neo4j_auth.txt`:
```
neo4j/your_secure_password
```

Update `docker-compose.yml`:
```yaml
environment:
  - NEO4J_AUTH_FILE=/run/secrets/neo4j_auth
secrets:
  neo4j_auth:
    file: ./secrets/neo4j_auth.txt
```

### Enable SSL/TLS

```yaml
environment:
  - NEO4J_server_https_enabled=true
  - NEO4J_server_bolt_tls_level=REQUIRED
volumes:
  - ./certs:/var/lib/neo4j/certificates
```

### Regular Backups

Add to crontab:
```bash
0 2 * * * docker exec neo4j-baziev neo4j-admin database dump neo4j --to-path=/data/backup/$(date +\%Y\%m\%d).dump
```

### Monitoring

```bash
# Resource usage
docker stats neo4j-baziev

# Disk usage
docker exec neo4j-baziev du -sh /data

# Active connections
docker exec neo4j-baziev cypher-shell -u neo4j -p password \
  "CALL dbms.listConnections() YIELD connectionId, connector RETURN count(*)"
```

## Additional Resources

- [Neo4j Docker Documentation](https://neo4j.com/docs/operations-manual/current/docker/)
- [APOC Documentation](https://neo4j.com/labs/apoc/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
