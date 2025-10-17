# Task Management Index

**Last Updated**: 2025-10-18

This directory contains all project tasks organized by status.

---

## 📁 Directory Structure

```
tasks/
├── TASK_INDEX.md          # This file - master task index
├── todo/                  # Active tasks to be completed
│   ├── REFACTORING_PLAN.md
│   └── REFACTORING_IMPLEMENTATION_DETAILS.md
└── done/                  # Completed tasks (archived)
    └── (completed tasks moved here)
```

---

## 📋 Active Tasks (todo/)

### 1. Backend/Frontend Refactoring
**Status**: Ready to Execute
**Files**:
- `todo/REFACTORING_PLAN.md` - High-level plan and overview
- `todo/REFACTORING_IMPLEMENTATION_DETAILS.md` - Detailed code specifications

**Description**: Complete reorganization of codebase with clean separation between backend and frontend.

**Key Objectives**:
- Split 2,083-line `api_server.py` into modular components
- Create `backend/` directory with organized structure
- Create `frontend/` directory for React app
- Implement BatchService class for batch generation
- Extract database models into dedicated module
- Create 5 focused route modules

**Estimated Duration**: ~2.5 hours

**Dependencies**: None

**Next Steps**:
1. User approval to proceed
2. Execute all 40 tasks continuously
3. Test thoroughly
4. Move to done/ upon completion

---

## ✅ Completed Tasks (done/)

### 1. Sample Type Balance Feature
**Completed**: 2025-10-18
**Description**: Added "balance" option to sample_type filter to automatically cycle through all 4 sample types (case_analysis, educational, client_interaction, statutory_interpretation) during generation.

**Changes Made**:
- Updated `config.py` with balance option
- Modified batch generation logic to cycle through sample types
- Updated single generation to randomly select type when "balance" used
- Added validation to prevent "balance" from reaching generation service directly

---

## 📝 Task Workflow

### Creating a New Task
1. Create task document in `tasks/todo/[TASK_NAME].md`
2. Update this index with task details
3. Add task to active tasks section

### Task Template
```markdown
# [Task Name]

**Date Created**: YYYY-MM-DD
**Priority**: High/Medium/Low
**Status**: Not Started/In Progress/Blocked

## Objective
[Clear description of what needs to be accomplished]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Steps
1. Step 1
2. Step 2

## Dependencies
- Depends on: [Task name]
- Blocks: [Task name]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
[Any additional context or notes]
```

### Completing a Task
1. Mark all acceptance criteria as complete
2. Update this index (move from Active to Completed section)
3. Move task file from `todo/` to `done/`
4. Add completion date and summary

---

## 🏷️ Task Categories

### Code Quality & Refactoring
- Backend/Frontend Refactoring (Active)

### Features
- Sample Type Balance Feature (Completed)

### Bug Fixes
- (None currently)

### Documentation
- (None currently)

### Testing
- (None currently)

### DevOps
- (None currently)

---

## 📊 Task Statistics

**Total Tasks**: 2
**Active**: 1 (50%)
**Completed**: 1 (50%)
**Blocked**: 0 (0%)

**By Priority**:
- High: 1
- Medium: 0
- Low: 0

---

## 🔍 Quick Reference

### Finding Tasks
- **All active tasks**: `ls tasks/todo/`
- **All completed tasks**: `ls tasks/done/`
- **Search by keyword**: `grep -r "keyword" tasks/`

### Task Status Codes
- 🆕 **Not Started** - Task created but not yet begun
- 🔄 **In Progress** - Currently being worked on
- ⏸️ **Blocked** - Waiting on dependencies or external factors
- ✅ **Completed** - Task finished and verified
- ❌ **Cancelled** - Task abandoned or no longer needed

---

## 📝 Notes

- All tasks should have clear acceptance criteria
- Tasks in `done/` should include completion summary
- Update this index whenever tasks are added, moved, or completed
- Large tasks should be broken down into smaller subtasks
- Each task file should be self-contained with all necessary information

---

## 🔗 Related Documentation

- Project root README: `/Users/rezazeraat/Desktop/Data/README.md`
- Legal Dashboard README: `/Users/rezazeraat/Desktop/Data/legal-dashboard/README.md`
- CLAUDE.md: `/Users/rezazeraat/Desktop/Data/CLAUDE.md`
- API Documentation: `/Users/rezazeraat/Desktop/Data/docs/API_USAGE.md`
