# how to run in terminal
# E.g: python task.py mark-done 3
# sys.argv[0]: the script name ("task.py")
# sys.argv[1]: the command ("mark-done")
# sys.argv[2]: the argument to the command ("3") 

import json
import sys
import os
from datetime import datetime

FILE_NAME = 'tasks.json'

def load_tasks():
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_tasks(tasks):
    with open(FILE_NAME, 'w') as f:
        json.dump(tasks, f, indent=4)

def add_task(description):
    tasks = load_tasks()
    new_id = 1 if not tasks else max(t['id'] for t in tasks) + 1
    
    new_task = {
        "id": new_id,
        "description": description,
        "status": "todo",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Task added successfully (ID: {new_id})")

def mark_status(task_id, status):
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == int(task_id):
            task["status"] = status
            task["updatedAt"] = datetime.now().isoformat()
            found = True
    if not found:
        print("No ID available.")
        return
    save_tasks(tasks)
    print("Tasks successfully updated.")   

def delete_task(task_id):
    tasks = load_tasks()
    before = len(tasks)

    tasks = [task for task in tasks if task["id"] != int(task_id)]
    if len(tasks) == before:
        print("No task was deleted.")
        return

    save_tasks(tasks)
    print("Deleted task successfully.")

def update_task(task_id, new_description):
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == int(task_id):
            task["description"] = new_description
            task["updatedAt"] = datetime.now().isoformat()
            found = True
    if not found:
        print("No ID available.")
        return
    save_tasks(tasks)
    print("Tasks successfully updated.")      

def list_tasks(status=None):
    tasks = load_tasks()
    matching = [task for task in tasks if status is None or task["status"] == status]

    if not matching:
        if status is None:
            print("No tasks found.")
        else:
            print(f"No tasks with status '{status}'.")
        return

    for task in matching:
        print(f"ID: {task["id"]}")
        print(f"Description: {task["description"]}")
        print(f"Status: {task["status"]}")
        print()

def parse_id(raw):
    try:
        return int(raw)
    except ValueError:
        print(f"Invalid ID: '{raw}'. The ID must be a number.")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python task.py [command] [arguments]")
        return

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("Usage: python task.py add [description]")
            return
        add_task(sys.argv[2])
    elif command == "mark-done":
        if len(sys.argv) < 3:
            print("Usage: python task.py mark-done [id]")
            return
        task_id = parse_id(sys.argv[2])
        if task_id is None:
            return
        mark_status(task_id, "done")
    elif command == "mark-in-progress":
        if len(sys.argv) < 3:
            print("Usage: python task.py mark-in-progress [id]")
            return
        task_id = parse_id(sys.argv[2])
        if task_id is None:
            return
        mark_status(task_id, "in-progress")
    elif command == "mark-blocked":
        if len(sys.argv) < 3:
            print("Usage: python task.py mark-blocked [id]")
            return
        task_id = parse_id(sys.argv[2])
        if task_id is None:
            return
        mark_status(task_id, "blocked")
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python task.py delete [id]")
            return
        task_id = parse_id(sys.argv[2])
        if task_id is None:
            return
        delete_task(task_id)
    elif command == "update":
        if len(sys.argv) < 4:
            print("Usage: python task.py update [id] [new description]")
            return
        task_id = parse_id(sys.argv[2])
        if task_id is None:
            return
        update_task(task_id, sys.argv[3])
    elif command == "list":
        list_tasks(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print("Unknown command.")
    

if __name__ == "__main__":
    main()