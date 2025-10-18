# PostgreSQL Migration

**Date Created**: 2025-10-18
**Priority**: High
**Status**: Not Started

---

## Objective

Migrate from SQLite to PostgreSQL for batch history tracking and improved performance/scalability.

---

## Requirements

- [ ] Add PostgreSQL service to docker-compose.yml
- [ ] Update backend database configuration
- [ ] Create PostgreSQL database and tables
- [ ] Migrate existing data from SQLite
- [ ] Update environment variables
- [ ] Test batch operations with PostgreSQL

---

## Steps

### 1. Add PostgreSQL to docker-compose.yml

```yaml
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=legal_dashboard
      - POSTGRES_USER=legal_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - legal-dashboard-network

volumes:
  postgres_data:
  portainer_data:
```

### 2. Update backend/config.py

Change from:
```python
DATABASE_URI = f'sqlite:///{Path(__file__).parent / "data" / "batches.db"}'
```

To:
```python
DATABASE_URI = os.getenv(
    'DATABASE_URL',
    'postgresql://legal_user:password@postgres:5432/legal_dashboard'
)
```

### 3. Update .env.example and .env

Add:
```env
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://legal_user:password@postgres:5432/legal_dashboard
```

### 4. Update backend/Dockerfile

Add PostgreSQL client library:
```dockerfile
RUN pip install --no-cache-dir \
    flask flask-cors flask-sqlalchemy polars pyarrow \
    groq cerebras_cloud_sdk tiktoken huggingface_hub \
    psycopg2-binary
```

### 5. Create tables on startup

Backend will auto-create tables using SQLAlchemy's `db.create_all()`.

### 6. Migrate existing data (optional)

If there's existing SQLite data to migrate:
```python
import sqlite3
from sqlalchemy import create_engine
# Migration script to copy data from SQLite to PostgreSQL
```

---

## Acceptance Criteria

- [ ] PostgreSQL service running in Docker
- [ ] Backend connects to PostgreSQL successfully
- [ ] Batch history tables created
- [ ] Batch generation creates records in PostgreSQL
- [ ] Batch history retrieval works
- [ ] No SQLite references remaining in backend

---

## Dependencies

- Docker Compose setup completed
- Backend structure finalized
- `.env` file configured

---

## Estimated Duration

~1 hour

**Breakdown**:
- Update docker-compose.yml: 10 min
- Update backend config: 10 min
- Update Dockerfile: 5 min
- Test and verify: 30 min
- Migration script (if needed): 5 min

---

## Benefits

- Better performance for concurrent operations
- Improved scalability for production
- Full ACID compliance
- Better support for complex queries
- Production-ready database

---

## Notes

- Use PostgreSQL 15 (latest stable)
- Use alpine variant for smaller image size
- Password should be in .env (not hardcoded)
- Data persists in postgres_data volume
- Can still use SQLite for development if needed

---

## Rollback Plan

If PostgreSQL causes issues:
```yaml
# Revert to SQLite by commenting out postgres service
# and changing DATABASE_URI back to sqlite:///
```
