import json
import os
from datetime import date
import argparse
import calendar
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
EXPENSES_FILE = os.path.join(HERE, "expenses.json")
BUDGETS_FILE = os.path.join(HERE, "budgets.json")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        # with open(...) as f: open it, call it f, and close it automatically when this indented block ends
        # no need to f.close() at all
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"Warning: could not read {path}, starting fresh.")
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_expenses():
    return load_json(EXPENSES_FILE, [])

def save_expenses(expenses):
    save_json(EXPENSES_FILE, expenses)

def load_budgets():
    return load_json(BUDGETS_FILE, {})

def save_budgets(budgets):
    save_json(BUDGETS_FILE, budgets)

def next_id(expenses):
    biggest = 0
    for expense in expenses:
        if expense["id"] > biggest:
            biggest = expense["id"]
    return biggest+1

def add_expense(description, amount, category):
    expenses = load_expenses()
    expense = {
        "id": next_id(expenses),
        # isoformat(): year-month-day
        "date": date.today().isoformat(),
        "description": description,
        "amount": amount,
        "category": category
    }
    expenses.append(expense)
    save_expenses(expenses)
    return expense

# unpack args, call it, print a message
# take the CLI's format (a Namespace) and converts it into the format your logic wants
def cmd_add(args):
    # args.description -> 'coffee',  args.amount -> 4.5
    expense = add_expense(args.description, args.amount, args.category)
    # expense -> {'id': 3, 'date': '2026-08-12', 'description': 'coffee', 'amount': 4.5}
    print(f"Expense added successfully (ID: {expense['id']})")
    # prints: Expense added successfully (ID: 3)

    # re-read the saved list so the warning counts the expense we just added
    today = date.today()
    check_budget(load_expenses(), today.year, today.month)
    return 0


def money(amount):
    # Format a number as money, e.g. 1234.5 -> '$1234.50'
    # , adds thousands separators
    return f"${amount:,.2f}"


def cmd_list(args):
    expenses = load_expenses()

    if args.category is not None:
        # .get(key, fallback) returns the fallback only when the key is missing,
        # so rows added before categories existed count as "General"
        expenses = [e for e in expenses
                    if e.get("category", "General").lower() == args.category.lower()]

    if not expenses:
        print("No expenses to show.")
        return 0

    print(f"{'ID':<4} {'Date':<12} {'Category':<14} {'Description':<30} {'Amount':>10}")
    for expense in expenses:
        print(f"{expense['id']:<4} {expense['date']:<12} "
              f"{expense.get('category', 'General'):<14} "
              f"{expense['description']:<30} {money(expense['amount']):>10}")
    return 0

def valid_month(value):
    try:
        month = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a whole number")
    if month < 1 or month > 12:
        raise argparse.ArgumentTypeError("month must be between 1 and 12")
    
    return month

def positive_amount(value):
    try:
        amount = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a number")
    if amount <= 0:
        raise argparse.ArgumentTypeError("amount must be greater than 0")
    return round(amount, 2)

def month_key(year, month):
    return f"{year}-{month:02d}"

def month_total(expenses, year, month):
    prefix = month_key(year, month)
    total = 0
    for expense in expenses:
        if expense["date"].startswith(prefix):
            total += expense["amount"]
    return total

def check_budget(expenses, year, month):
    limit = load_budgets().get(month_key(year, month))
    if limit is None:
        # no budget set for this month
        return                       
    spent = month_total(expenses, year, month)
    if spent > limit:
        over = spent - limit
        print(f"Warning: {calendar.month_name[month]} spending is {money(spent)}, "
              f"{money(over)} over your {money(limit)} budget.")


def cmd_set_budget(args):
    budgets = load_budgets()
    key = month_key(date.today().year, args.month)
    # add or overwrite that month's entry
    budgets[key] = args.amount
    save_budgets(budgets)
    print(f"Budget for {calendar.month_name[args.month]} set to {money(args.amount)}")
    return 0

def cmd_summary(args):
    expenses = load_expenses()
    total = 0

    year = date.today().year
    label = "Total expenses"

    if args.month is not None:
        prefix = month_key(year, args.month)
        expenses = [e for e in expenses if e["date"].startswith(prefix)]
        label += f" for {calendar.month_name[args.month]}"

    if args.category is not None:
        expenses = [e for e in expenses
                    if e.get("category", "General").lower() == args.category.lower()]
        label += f" in {args.category}"

    for expense in expenses:
        total += expense["amount"]
    print(f"{label}: {money(total)}")

    # a month's budget only makes sense against that whole month, not one category
    if args.month is not None and args.category is None:
        limit = load_budgets().get(month_key(year, args.month))
        if limit is not None:
            if total > limit:
                print(f"Budget: {money(limit)} - over by {money(total - limit)}")
            else:
                print(f"Budget: {money(limit)} - {money(limit - total)} left")
    return 0

def find_expense(expenses, expense_id):
    for expense in expenses:
        if expense["id"] == expense_id:
            return expense
    return None

def cmd_delete(args):
    expenses = load_expenses()
    expense = find_expense(expenses, args.id)
    if expense is None:
        print(f"Error: no expense found with ID {args.id}")
        return 1
    expenses.remove(expense)
    save_expenses(expenses)       
    print("Expense deleted successfully")
    return 0

def cmd_update(args):
    expenses = load_expenses()
    expense = find_expense(expenses, args.id)
    if expense is None:
        print(f"Error: no expense found with ID {args.id}")
        return 1

    # nothing to change: say so rather than reporting a silent success
    if args.description is None and args.amount is None and args.category is None:
        print("Error: nothing to update. Pass --description, --amount or --category.")
        return 1

    if args.description is not None:
        expense["description"] = args.description
    if args.amount is not None:
        expense["amount"] = args.amount
    if args.category is not None:
        expense["category"] = args.category

    # expense IS the dict inside expenses, so the list is already updated
    save_expenses(expenses)
    print(f"Expense updated successfully (ID: {expense['id']})")
    return 0

def cmd_export(args):
    expenses = load_expenses()
    columns = ["id", "date", "description", "category", "amount"]

    # newline="" is required on Windows or every other line comes out blank
    with open(args.file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for expense in expenses:
            writer.writerow({
                "id": expense["id"],
                "date": expense["date"],
                "description": expense["description"],
                "category": expense.get("category", "General"),
                "amount": expense["amount"],
            })
    print(f"Exported {len(expenses)} expenses to {args.file}")
    return 0


def build_parser():
    # prog is the name shown in help/error messages 
    parser = argparse.ArgumentParser(prog="expense-tracker")
    # required=True - running the program with no sub-command is an error rather than silently doing nothing
    subparsers = parser.add_subparsers(dest="command", required=True)
    # registers the word "add" as a valid sub-command 
    # and returns a whole new parser that only handles what comes after that word
    # help text appears in expense-tracker --help
    add = subparsers.add_parser("add", help="add a new expense")
    listing = subparsers.add_parser("list", help="list all expenses")
    summary = subparsers.add_parser("summary", help="summary of all expenses")
    delete = subparsers.add_parser("delete", help="delete an expense")
    update = subparsers.add_parser("update", help="update an expense")
    budget = subparsers.add_parser("set-budget", help="set budget for a month")
    export = subparsers.add_parser("export", help="export expenses into a CSV file")


    add.add_argument("--description", required=True)
    add.add_argument("--amount", type=positive_amount, required=True)
    add.add_argument("--category", default="General")
    listing.add_argument("--category")
    summary.add_argument("--month", type=valid_month)
    summary.add_argument("--category")
    delete.add_argument("--id", type=int, required=True)
    update.add_argument("--id", type=int, required=True)
    update.add_argument("--description")
    update.add_argument("--amount", type=positive_amount)
    update.add_argument("--category")
    budget.add_argument("--month", type=valid_month, required=True)
    budget.add_argument("--amount", type=positive_amount, required=True)
    export.add_argument("--file", default="expenses.csv")

    
    add.set_defaults(func=cmd_add)
    listing.set_defaults(func=cmd_list)
    summary.set_defaults(func=cmd_summary)
    delete.set_defaults(func=cmd_delete)
    update.set_defaults(func=cmd_update)
    budget.set_defaults(func=cmd_set_budget)
    export.set_defaults(func=cmd_export)


    return parser

def main():
    parser = build_parser()
    # read strings and hands back a Namespace with converted values
    args = parser.parse_args()
    # runs the cmd function argparse selected
    return args.func(args)

# Only run main() if this file was launched directly
if __name__ == "__main__":
    raise SystemExit(main())