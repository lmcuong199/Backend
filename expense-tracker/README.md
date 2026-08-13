# Expense Tracker

A simple command line expense tracker to manage your finances.

Solution to the [roadmap.sh Expense Tracker project](https://roadmap.sh/projects/expense-tracker).

## Features

- Add, update and delete expenses
- View all expenses, or filter them by category
- View a summary of all expenses, of a single month, or of a category
- Set a monthly budget and get warned when you go over it
- Export expenses to a CSV file

## Requirements

Python 3.8 or newer. No third-party packages — everything uses the standard
library (`argparse`, `json`, `csv`, `calendar`, `datetime`).

## Usage

All commands are run as `python expense.py <command>`.

### Add an expense

```bash
$ python expense.py add --description "Lunch" --amount 20
# Expense added successfully (ID: 1)

$ python expense.py add --description "Pizza" --amount 15 --category Food
# Expense added successfully (ID: 4)
```

`--category` is optional and defaults to `General`.

### List expenses

```bash
$ python expense.py list
# ID   Date         Category       Description                        Amount
# 1    2026-08-12   Food           Big lunch                          $25.00
# 2    2026-08-12   General        Dinner                             $10.50
# 3    2026-08-12   General        Taxi                               $12.00
# 4    2026-08-13   Food           Pizza                              $15.00
# 5    2026-08-13   Transport      Bus pass                           $30.00
```

Filter by category (case-insensitive):

```bash
$ python expense.py list --category food
# ID   Date         Category       Description                        Amount
# 1    2026-08-12   Food           Big lunch                          $25.00
# 4    2026-08-13   Food           Pizza                              $15.00
```

### Update an expense

```bash
$ python expense.py update --id 1 --amount 25 --description "Big lunch"
# Expense updated successfully (ID: 1)
```

Pass any combination of `--description`, `--amount` and `--category`.
Fields you leave out are kept as they are.

### Delete an expense

```bash
$ python expense.py delete --id 2
# Expense deleted successfully
```

### View a summary

```bash
$ python expense.py summary
# Total expenses: $92.50
```

For a single month of the current year:

```bash
$ python expense.py summary --month 8
# Total expenses for August: $92.50
# Budget: $500.00 - $407.50 left
```

For a single category:

```bash
$ python expense.py summary --category Food
# Total expenses in Food: $40.00
```

The budget line only appears when a budget is set for that month.

### Set a monthly budget

```bash
$ python expense.py set-budget --month 8 --amount 50
# Budget for August set to $50.00
```

Once a budget is set, adding an expense that pushes you over it prints a warning:

```bash
$ python expense.py add --description "Pizza" --amount 15
# Expense added successfully (ID: 6)
# Warning: August spending is $107.50, $57.50 over your $50.00 budget.
```

And `summary --month` reports how far over you are:

```bash
$ python expense.py summary --month 8
# Total expenses for August: $107.50
# Budget: $50.00 - over by $57.50
```

### Export to CSV

```bash
$ python expense.py export
# Exported 7 expenses to expenses.csv

$ python expense.py export --file august.csv
# Exported 7 expenses to august.csv
```

Descriptions containing commas are quoted correctly:

```csv
id,date,description,category,amount
7,2026-08-13,"Lunch, with Ana",Food,18.0
```

### Help

```bash
$ python expense.py --help
$ python expense.py add --help
```

## Error handling

Invalid input is rejected before anything is written to disk:

```bash
$ python expense.py add --description "Refund" --amount -5
# expense-tracker add: error: argument --amount: amount must be greater than 0

$ python expense.py summary --month 13
# expense-tracker summary: error: argument --month: month must be between 1 and 12

$ python expense.py summary --month abc
# expense-tracker summary: error: argument --month: 'abc' is not a whole number

$ python expense.py delete --id 99
# Error: no expense found with ID 99

$ python expense.py update --id 1
# Error: nothing to update. Pass --description, --amount or --category.
```

A corrupted data file produces a warning rather than a crash:

```bash
$ python expense.py list
# Warning: could not read expenses.json, starting fresh.
# No expenses to show.
```

Exit codes follow the usual convention:

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | The command ran but failed (e.g. no such ID) |
| 2 | Invalid command line arguments |

## Data storage

| File | Contents |
| --- | --- |
| `expenses.json` | A list of expenses, one object each |
| `budgets.json` | A month-to-limit lookup, e.g. `{"2026-08": 50.0}` |

Both files are created next to `expense.py` on first use, so the app reads the
same data no matter which folder you run it from. Both are gitignored, along
with any exported CSV files.
