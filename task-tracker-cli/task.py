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

def mark_done (tasks):
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == int(sys.argv[2]):
            task["status"] = "done"
            found = True

    save_tasks(tasks)
    if (found == False):
        print(f"No ID available.")
    else:
        print(f"Tasks successfully updated.")

# def list_tasks(tasks, description, status):
#    print(f"ID:")
#    print(f"Description:")    
#    print(f"Status": {}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python task.py add [description]")
        return

    command = sys.argv[1]
    
    if command == "add":
        add_task(sys.argv[2])
    elif command == "mark-done":
        mark_done(sys.argv[2])
    else:
        print("Unknown command.")
    

if __name__ == "__main__":
    main()