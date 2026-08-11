import json
import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
EXPENSES_FILE = os.path.join(HERE, "expenses.json")

def save_expenses(expenses):
    # with open(...) as f: open it, call it f, and close it automatically when this indented block ends
    # no need to f.close() at all
    with open(EXPENSES_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)

def load_expenses():
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, "r", encoding="utf-8") as f:
            expenses = json.load(f)
            return expenses
    else:
        return []

def next_id(expenses):
    biggest = 0
    for expense in expenses:
        if expense["id"] > biggest:
            biggest = expense["id"]
    return biggest+1

def add_expense(description, amount):
    expenses = load_expenses()
    expense = {
        "id": next_id(expenses),
        # isoformat(): year-month-day
        "date": date.today().isoformat(),
        "description": description,
        "amount": amount
    }
    expenses.append(expense)
    save_expenses(expenses)
    return expense
