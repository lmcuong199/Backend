import json
import os
from datetime import date
import argparse
import calendar

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

# unpack args, call it, print a message
# take the CLI's format (a Namespace) and converts it into the format your logic wants
def cmd_add(args):
    # args.description -> 'coffee',  args.amount -> 4.5
    expense = add_expense(args.description, args.amount)
    # expense -> {'id': 3, 'date': '2026-08-12', 'description': 'coffee', 'amount': 4.5}
    print(f"Expense added successfully (ID: {expense['id']})")
    # prints: Expense added successfully (ID: 3)


def money(amount):
    # Format a number as money, e.g. 1234.5 -> '$1234.50'
    # , adds thousands separators
    return f"${amount:,.2f}"


def cmd_list(args):
    expenses = load_expenses()
    if not expenses:
        print("No expenses to show.")
        return

    print(f"{'ID':<4} {'Date':<12} {'Description':<36} {'Amount':>10}")
    for expense in expenses:
        print(f"{expense['id']:<4} {expense['date']:<12} {expense['description']:<36} {money(expense['amount']):>10}")

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

def cmd_summary(args):
    expenses = load_expenses()
    total = 0

    year = date.today().year
    label = "Total expenses"

    if args.month is not None:
        prefix = f"{year}-{args.month:02d}"
        expenses = [e for e in expenses if e['date'].startswith(prefix)]
        label += f" for {calendar.month_name[args.month]}"

    for expense in expenses:
        total += expense['amount']
    print(f"{label}: {money(total)}")

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

    add.add_argument("--description", required=True)
    add.add_argument("--amount", type=positive_amount, required=True)
    summary.add_argument("--month", type=valid_month)
    
    add.set_defaults(func=cmd_add)
    listing.set_defaults(func=cmd_list)
    summary.set_defaults(func=cmd_summary)

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