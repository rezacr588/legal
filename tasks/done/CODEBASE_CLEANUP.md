# Codebase Cleanup - Remove Legacy Code

**Date Created**: 2025-10-18
**Priority**: Medium
**Status**: Not Started

---

## Objective

Clean up the codebase by removing duplicate files, legacy code, and consolidating redundant documentation now that the refactoring is complete.

---

## Requirements

- ✅ Remove duplicate files (old structure vs new structure)
- ✅ Archive or delete legacy code that's been replaced
- ✅ Consolidate duplicate documentation
- ✅ Keep legal-dashboard/ as backup until fully validated
- ✅ Update .gitignore if needed
- ✅ Document what was removed and why

---

## Files/Directories to Review

### 1. Potential Duplicates

**Backend Code:**
- `legal-dashboard/api_server.py` (2,083 lines) - Still in use via backend/app.py wrapper
- `legal-dashboard/config.py` - Duplicated in `backend/config.py`
- `legal-dashboard/services/` - Duplicated in `backend/services/`
- `legal-dashboard/utils/` - Duplicated in `backend/utils/`
- `legal-dashboard/models/` - Duplicated in `backend/models/`

**Data Files:**
- `train.parquet` (root) - Duplicated in `backend/data/train.parquet`
- `legal-dashboard/train.parquet` - Duplicated in `backend/data/train.parquet`
- `legal-dashboard/batches.db` - Moved to `backend/data/batches.db`

**Frontend Code:**
- `legal-dashboard/src/` - Duplicated in `frontend/src/`
- `legal-dashboard/public/` - Duplicated in `frontend/public/`
- `legal-dashboard/package.json` - Duplicated in `frontend/package.json`
- `legal-dashboard/vite.config.js` - Duplicated in `frontend/vite.config.js`

**Scripts:**
- `start_apps.sh` (root) - Replaced by `scripts/start_all.sh`
- `start_service.sh` (root) - Replaced by Docker Compose
- `stop_service.sh` (root) - Replaced by `scripts/stop_all.sh`

**Documentation:**
- Multiple README files in different locations
- Redundant implementation guides

### 2. Legacy Files to Archive

Files that were part of the old structure but may have historical value:

- Old startup scripts
- Previous configuration files
- Migration scripts (if any)

---

## Proposed Cleanup Plan

### Phase 1: Create Archive Directory (SAFE)

Create `archive/` directory and move (not delete) old files:

```bash
mkdir -p archive/old-structure
mv legal-dashboard archive/old-structure/
mv start_apps.sh archive/old-structure/ 2>/dev/null
mv start_service.sh archive/old-structure/ 2>/dev/null
mv stop_service.sh archive/old-structure/ 2>/dev/null
```

**Reasoning**: Keep backups until new structure is fully validated in production.

### Phase 2: Document Archive Contents

Create `archive/ARCHIVE_README.md`:
```markdown
# Archived Files

This directory contains the old codebase structure before refactoring.

**Date Archived**: 2025-10-18
**Reason**: Replaced by new backend/ and frontend/ structure with Docker Compose

## Contents
- old-structure/legal-dashboard/ - Original monolithic structure
- old-structure/start_apps.sh - Replaced by scripts/start_all.sh
- ...

## Can These Be Deleted?
Yes, after 30 days of running new structure in production without issues.

## How to Restore
If needed, can copy files back from archive/.
```

### Phase 3: Update .gitignore

Add archive directory to .gitignore:
```
# Archived old code
archive/
```

### Phase 4: Clean Root Directory

Keep root directory clean:
```
Data/
├── backend/          # New structure
├── frontend/         # New structure
├── scripts/          # New structure
├── archive/          # Old structure (gitignored)
├── tasks/
├── docs/
├── docker-compose.yml
├── .env.example
├── README.md
└── DOCKER_README.md
```

### Phase 5: Consolidate Documentation

**Keep**:
- `README.md` (main project readme)
- `DOCKER_README.md` (Docker setup)
- `DOCKER_MONITORING.md` (monitoring setup)
- `REFACTORING_SUMMARY.md` (what was done)
- `ENVIRONMENT_SETUP.md` (API keys setup)

**Consolidate/Remove**:
- Multiple copies of API documentation
- Redundant setup guides
- Old implementation plans (keep in tasks/done/)

---

## Acceptance Criteria

- [ ] Archive directory created with old structure
- [ ] `archive/ARCHIVE_README.md` created documenting what's archived
- [ ] Root directory cleaned (only new structure visible)
- [ ] Duplicate data files removed (keep only backend/data/)
- [ ] .gitignore updated to exclude archive/
- [ ] Documentation consolidated (no duplicate guides)
- [ ] CLEANUP_SUMMARY.md created documenting what was removed
- [ ] New structure tested and working after cleanup

---

## Safety Measures

### Before Starting
1. ✅ Ensure git is initialized and all changes committed
2. ✅ Create full backup: `tar -czf backup-before-cleanup.tar.gz .`
3. ✅ Test new structure works: `docker-compose up`

### During Cleanup
1. Move files to `archive/` instead of deleting
2. Keep archive/ until new structure validated (30 days)
3. Document every file moved

### After Cleanup
1. Test all services still work
2. Verify no broken import paths
3. Check documentation links still valid

---

## Rollback Plan

If something breaks after cleanup:

```bash
# Stop services
docker-compose down

# Restore from archive
cp -r archive/old-structure/legal-dashboard .

# Or restore from backup
tar -xzf backup-before-cleanup.tar.gz

# Restart services
docker-compose up
```

---

## Estimated Duration

~45 minutes

**Breakdown**:
- Create backup: 5 min
- Create archive directory and move files: 15 min
- Update .gitignore and documentation: 10 min
- Test new structure: 10 min
- Create cleanup summary: 5 min

---

## Benefits After Cleanup

1. **Cleaner Repository**: No confusion about which files to use
2. **Faster Navigation**: Less clutter in root directory
3. **Smaller Repo Size**: Remove duplicate large files (parquet, node_modules)
4. **Clear Structure**: Obviously separated backend/frontend
5. **Better Onboarding**: New developers see clean structure
6. **Easier Maintenance**: No need to update files in multiple locations

---

## Files That Will Remain

**Active Files (After Cleanup)**:
```
Data/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models/
│   ├── services/
│   ├── utils/
│   ├── data/
│   │   ├── train.parquet
│   │   └── batches.db
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── scripts/
│   ├── start_all.sh
│   ├── start_backend.sh
│   ├── start_frontend.sh
│   └── stop_all.sh
├── tasks/
├── docs/
├── tests/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── DOCKER_README.md
└── REFACTORING_SUMMARY.md
```

**Archived Files**:
```
archive/
└── old-structure/
    ├── legal-dashboard/    (entire old directory)
    ├── train.parquet       (duplicate)
    ├── start_apps.sh       (replaced)
    ├── start_service.sh    (replaced)
    └── stop_service.sh     (replaced)
```

---

## Special Considerations

### Keep legal-dashboard/ Temporarily

Since `backend/app.py` currently wraps `legal-dashboard/api_server.py`, we need to:

**Option A (Safer)**: Keep legal-dashboard in archive but accessible
```python
# backend/app.py still references it
sys.path.insert(0, str(parent_dir / "archive" / "old-structure" / "legal-dashboard"))
```

**Option B (Future)**: Complete route breakout (Phase 2 of refactoring)
- Fully migrate all routes to backend/routes/
- Then legal-dashboard can be fully archived

**Recommendation**: Use Option A for now, plan Option B for later.

---

## Documentation Updates

After cleanup, update these files:

1. **README.md**: Update file structure diagram
2. **DOCKER_README.md**: Ensure paths are correct
3. **CLAUDE.md**: Update directory structure section
4. **tasks/TASK_INDEX.md**: Mark cleanup as complete

---

## Notes

- Keep archive/ for at least 30 days of production use
- Can add to .dockerignore to prevent archive from being copied to containers
- Consider creating CHANGELOG.md documenting the cleanup
- After 30 days with no issues, can delete archive/ entirely

---

## Success Metrics

- [ ] Root directory has <15 files/folders (not including hidden files)
- [ ] No duplicate .parquet files
- [ ] No duplicate node_modules/
- [ ] All services start with `docker-compose up`
- [ ] All documentation links work
- [ ] Repository size reduced by >500MB

---

## Related Tasks

- Depends on: Backend/Frontend Refactoring (Completed)
- Blocks: None
- Related: Docker Monitoring Setup (can run in parallel)

---

## References

- Refactoring Summary: `REFACTORING_SUMMARY.md`
- Original Structure: `archive/old-structure/` (after cleanup)
- Git Best Practices: Keep history, archive don't delete
