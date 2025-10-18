# Docker Container Monitoring & Management Setup

**Date Created**: 2025-10-18
**Priority**: Medium
**Status**: Not Started

---

## Objective

Set up web-based tools for monitoring Docker container logs and managing containers (stop/restart/inspect) without using CLI commands.

---

## Requirements

- ✅ Real-time log monitoring for backend and frontend containers
- ✅ Ability to stop/restart containers via web interface
- ✅ Container resource usage monitoring (CPU, memory)
- ✅ Easy access without complex CLI commands
- ✅ Lightweight and minimal resource overhead
- ✅ Works alongside existing docker-compose.yml

---

## Proposed Solution

Use **Portainer** + **Dozzle** combination:

### 1. Portainer (Container Management)
- **Purpose**: Full Docker management GUI
- **Features**: Start/stop/restart containers, view stats, manage networks/volumes
- **Access**: Web UI at http://localhost:9000
- **Resource**: ~50MB RAM

### 2. Dozzle (Log Viewer)
- **Purpose**: Real-time log monitoring
- **Features**: Multi-container logs, search, filtering, auto-refresh
- **Access**: Web UI at http://localhost:8080
- **Resource**: ~10MB RAM

---

## Implementation Steps

### Step 1: Add Monitoring Services to docker-compose.yml

Add two new services to the existing `docker-compose.yml`:

```yaml
  # Docker Management UI
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    networks:
      - legal-dashboard-network

  # Log Monitoring UI
  dozzle:
    image: amir20/dozzle:latest
    container_name: dozzle
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - DOZZLE_LEVEL=info
      - DOZZLE_TAILSIZE=300
      - DOZZLE_FILTER=name=backend,name=frontend
    networks:
      - legal-dashboard-network

volumes:
  portainer_data:
```

### Step 2: Create Docker Management Guide

Create `DOCKER_MONITORING.md` with:
- How to access Portainer
- How to access Dozzle
- Common management tasks
- Troubleshooting tips

### Step 3: Update docker-compose.yml

Merge the new services into existing docker-compose.yml

### Step 4: Update Documentation

Update the following files:
- `DOCKER_README.md` - Add monitoring section
- `README.md` - Add monitoring links
- `.gitignore` - Ensure portainer data is ignored

### Step 5: Test the Setup

- Start services: `docker-compose up -d`
- Access Portainer: http://localhost:9000
- Access Dozzle: http://localhost:8080
- Test stop/restart functionality
- Verify log streaming

---

## Acceptance Criteria

- [ ] Portainer accessible at http://localhost:9000
- [ ] Dozzle accessible at http://localhost:8080
- [ ] Can view real-time logs for backend and frontend
- [ ] Can stop/restart containers from Portainer
- [ ] Can view container resource usage (CPU/memory)
- [ ] Documentation created (DOCKER_MONITORING.md)
- [ ] DOCKER_README.md updated with monitoring section
- [ ] All services start with single `docker-compose up` command
- [ ] Monitoring services restart automatically on failure

---

## Alternative Options Considered

### Option 1: Docker Desktop Built-in Dashboard
- **Pros**: Already installed, no setup
- **Cons**: Only on desktop, not available on servers, limited features

### Option 2: Lazydocker (TUI)
- **Pros**: Lightweight, keyboard-driven
- **Cons**: Still CLI-based (terminal UI), learning curve

### Option 3: Grafana + Prometheus
- **Pros**: Production-grade monitoring
- **Cons**: Overkill for development, complex setup, heavy resource usage

### Option 4: ctop (CLI monitoring)
- **Pros**: Simple, lightweight
- **Cons**: CLI-only, no log viewing

**Selected**: Portainer + Dozzle for best balance of features, ease of use, and resource efficiency.

---

## Benefits

1. **No CLI Required**: Everything via web browser
2. **Real-time Logs**: See logs as they happen
3. **Easy Troubleshooting**: Quickly restart failing containers
4. **Resource Monitoring**: See if containers are using too much CPU/memory
5. **Multi-container View**: See all containers at once
6. **Search/Filter**: Find specific log entries easily
7. **Persistent**: Survives container restarts

---

## Expected Outcome

After completion:
- Access http://localhost:8080 → See all container logs in real-time
- Access http://localhost:9000 → Manage all containers (stop/restart/inspect)
- Single command startup: `docker-compose up -d`
- No need to remember `docker logs`, `docker restart` commands

---

## Dependencies

- Docker and Docker Compose already installed
- Existing docker-compose.yml working
- Ports 8080 and 9000 available

---

## Estimated Duration

~30 minutes

**Breakdown**:
- Update docker-compose.yml: 5 min
- Create DOCKER_MONITORING.md: 10 min
- Update existing documentation: 5 min
- Test and verify: 10 min

---

## Notes

- Portainer requires initial setup (create admin user) on first access
- Dozzle is read-only (cannot modify containers, only view logs)
- Both services are production-ready and widely used
- Can be disabled by commenting out in docker-compose.yml if not needed
- Access URLs:
  - **Dozzle (Logs)**: http://localhost:8080
  - **Portainer (Management)**: http://localhost:9000
  - **Backend API**: http://localhost:5000
  - **Frontend UI**: http://localhost:5173

---

## Security Considerations

- Portainer has authentication (admin username/password)
- Dozzle has no authentication by default (consider adding if exposing to network)
- Both mount Docker socket (standard practice for management tools)
- Use reverse proxy with HTTPS for production deployments

---

## Future Enhancements

Optional additions after basic setup works:

1. **Email Alerts**: Configure Portainer to send email on container failures
2. **Authentication for Dozzle**: Add basic auth or OAuth
3. **Custom Dashboards**: Create Portainer templates for common tasks
4. **Log Export**: Configure log retention and export
5. **Multi-host**: Extend Portainer to manage multiple Docker hosts

---

## References

- Portainer Documentation: https://docs.portainer.io/
- Dozzle Documentation: https://dozzle.dev/
- Docker Compose Documentation: https://docs.docker.com/compose/
