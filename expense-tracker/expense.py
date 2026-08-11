import json
import os
from datetime import date
import argparse

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

def cmd_add(args):
    expense = add_expense(args.description, args.amount)
    print(f"Expense added successfully (ID: {expense['id']})")

def build_parser():
    parser = argparse.ArgumentParser(prog="expense-tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="add a new expense")
    add.add_argument("--description", required=True)
    add.add_argument("--amount", type=float, required=True)
    add.set_defaults(func=cmd_add)

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

# Only run main() if this file was launched directly
if __name__ == "__main__":
    main()