# Tasks Directory

This directory contains all project tasks organized by completion status.

## Structure

```
tasks/
├── README.md              # This file
├── TASK_INDEX.md          # Master index of all tasks
├── todo/                  # Active tasks
│   └── *.md              # Task documents
└── done/                  # Completed tasks
    └── *.md              # Archived task documents
```

## Quick Start

### View All Active Tasks
```bash
ls todo/
```

### View Task Index
```bash
cat TASK_INDEX.md
```

### Add a New Task
1. Create a task file in `todo/` directory
2. Update `TASK_INDEX.md` with task details
3. Follow the task template in `TASK_INDEX.md`

### Complete a Task
1. Mark task as complete
2. Move file from `todo/` to `done/`
3. Update `TASK_INDEX.md`

## Current Active Tasks

1. **Backend/Frontend Refactoring** - Complete codebase reorganization
   - File: `todo/REFACTORING_PLAN.md`
   - Status: Ready to Execute
   - Duration: ~2.5 hours

## Task Management Philosophy

- **Organized**: All tasks in one place with clear status
- **Trackable**: Easy to see what's done and what's pending
- **Documented**: Each task has full context and requirements
- **Auditable**: Completed tasks archived for reference

## Tips

- Keep task files focused and self-contained
- Update TASK_INDEX.md regularly
- Use clear, descriptive task names
- Include acceptance criteria in each task
- Archive completed tasks promptly
