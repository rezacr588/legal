#!/bin/bash

# Task Manager Script
# Helps manage tasks in the tasks/ directory

TASKS_DIR="/Users/rezazeraat/Desktop/Data/tasks"
TODO_DIR="$TASKS_DIR/todo"
DONE_DIR="$TASKS_DIR/done"
INDEX_FILE="$TASKS_DIR/TASK_INDEX.md"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo "Task Manager - Manage project tasks"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  list         List all active tasks"
    echo "  done         List all completed tasks"
    echo "  stats        Show task statistics"
    echo "  complete     Mark a task as complete (interactive)"
    echo "  help         Show this help message"
    echo ""
}

# Function to list active tasks
list_todo() {
    echo -e "${BLUE}=== Active Tasks ===${NC}"
    if [ -z "$(ls -A $TODO_DIR)" ]; then
        echo "No active tasks"
    else
        cd "$TODO_DIR"
        for task in *.md; do
            if [ -f "$task" ]; then
                echo -e "${GREEN}📝 $task${NC}"
            fi
        done
    fi
}

# Function to list completed tasks
list_done() {
    echo -e "${BLUE}=== Completed Tasks ===${NC}"
    if [ -z "$(ls -A $DONE_DIR)" ]; then
        echo "No completed tasks"
    else
        cd "$DONE_DIR"
        for task in *.md; do
            if [ -f "$task" ]; then
                echo -e "${GREEN}✅ $task${NC}"
            fi
        done
    fi
}

# Function to show statistics
show_stats() {
    todo_count=$(find "$TODO_DIR" -name "*.md" | wc -l | xargs)
    done_count=$(find "$DONE_DIR" -name "*.md" | wc -l | xargs)
    total=$((todo_count + done_count))

    echo -e "${BLUE}=== Task Statistics ===${NC}"
    echo -e "Total Tasks: ${YELLOW}$total${NC}"
    echo -e "Active: ${YELLOW}$todo_count${NC}"
    echo -e "Completed: ${GREEN}$done_count${NC}"

    if [ $total -gt 0 ]; then
        completion_rate=$((done_count * 100 / total))
        echo -e "Completion Rate: ${GREEN}$completion_rate%${NC}"
    fi
}

# Function to complete a task
complete_task() {
    echo -e "${BLUE}=== Mark Task as Complete ===${NC}"

    cd "$TODO_DIR"
    tasks=(*.md)

    if [ ${#tasks[@]} -eq 0 ] || [ ! -f "${tasks[0]}" ]; then
        echo "No active tasks to complete"
        return
    fi

    echo "Select task to mark as complete:"
    select task in "${tasks[@]}" "Cancel"; do
        if [ "$task" == "Cancel" ]; then
            echo "Cancelled"
            return
        elif [ -n "$task" ]; then
            echo -e "${YELLOW}Moving $task to done/${NC}"
            mv "$TODO_DIR/$task" "$DONE_DIR/"
            echo -e "${GREEN}✅ Task completed!${NC}"
            echo -e "${YELLOW}Don't forget to update TASK_INDEX.md${NC}"
            break
        fi
    done
}

# Main command handler
case "$1" in
    list)
        list_todo
        ;;
    done)
        list_done
        ;;
    stats)
        show_stats
        ;;
    complete)
        complete_task
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -n "$1" ]; then
            echo -e "${RED}Unknown command: $1${NC}"
            echo ""
        fi
        show_help
        ;;
esac
