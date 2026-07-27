# Task Tracker CLI

A command line task tracker that stores tasks in a local JSON file.

Project page: https://roadmap.sh/projects/task-tracker

Tasks are kept in `tasks.json`, created automatically on first use. No external dependencies —
standard library only.

## Requirements

- Python 3.12 or newer

(3.12+ is required because the code uses nested same-type quotes inside f-strings, e.g.
`f"ID: {task["id"]}"`, which was only made legal by [PEP 701](https://peps.python.org/pep-0701/).)

## Usage

```
python task.py [command] [arguments]
```

### Adding a task

```bash
python task.py add "Buy groceries"
# Task added successfully (ID: 1)
```

New tasks start with status `todo`. IDs are assigned automatically as one higher than the current
maximum.

### Updating a task

```bash
python task.py update 1 "Buy groceries and cook dinner"
# Tasks successfully updated.
```

### Deleting a task

```bash
python task.py delete 1
# Deleted task successfully.
```

### Changing status

```bash
python task.py mark-in-progress 1
python task.py mark-done 1
python task.py mark-blocked 1
# Tasks successfully updated.
```

`mark-blocked` is an extra beyond the project spec.

### Listing tasks

```bash
python task.py list                 # every task
python task.py list todo
python task.py list in-progress
python task.py list done
python task.py list blocked
```

Output:

```
ID: 1
Description: Buy groceries
Status: done

ID: 2
Description: Write the readme
Status: todo
```

## Task format

Each task is a JSON object with these fields:

| Field | Description |
|---|---|
| `id` | Unique integer identifier |
| `description` | What the task is |
| `status` | `todo`, `in-progress`, `done`, or `blocked` |
| `createdAt` | ISO 8601 timestamp of creation |
| `updatedAt` | ISO 8601 timestamp of last change |

Example `tasks.json`:

```json
[
    {
        "id": 1,
        "description": "Buy groceries",
        "status": "done",
        "createdAt": "2026-07-27T21:47:05.319526",
        "updatedAt": "2026-07-27T22:03:11.882140"
    }
]
```

## Error handling

| Situation | Result |
|---|---|
| No command given | Usage message |
| Unrecognised command | `Unknown command.` |
| Missing argument | Usage message for that command |
| Non-numeric ID | `Invalid ID: 'abc'. The ID must be a number.` |
| ID that doesn't exist | `No ID available.` / `No task was deleted.` |
| No tasks at all | `No tasks found.` |
| No tasks match a filter | `No tasks with status 'blocked'.` |
| Missing or corrupt `tasks.json` | Treated as an empty task list |

## Notes

`tasks.json` is written to the **current working directory**, not to the script's directory. Running
the script from a different folder will use a separate task list.
