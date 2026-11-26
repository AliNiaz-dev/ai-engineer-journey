"""
Main CLI entry point for the Python Expense Tracker.

This module owns:
- The interactive terminal menu (a pure function-based UI layer)
- Input helpers with full validation and graceful error handling
- Routing between all features (manager, reports, exporter, quiz)

Run from the project root:
    python -m expense_tracker.main
or, after editable install:
    expense-tracker
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from expense_tracker.exceptions import (
    DuplicateExpenseError,
    ExpenseNotFoundError,
    ExpenseTrackerError,
    StorageError,
    ValidationError,
)
from expense_tracker.exporter import CSVExporter
from expense_tracker.manager import ExpenseManager
from expense_tracker.models import Expense, validate_month
from expense_tracker.quiz import Quiz
from expense_tracker.reports import ReportPrinter
from expense_tracker.storage import JsonStorage

# ── Paths ─────────────────────────────────────────────────────────────────────
# Resolve relative to the project root (two parents above src/expense_tracker)
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[2]       # …/expense-tracker-cli/
_DATA_FILE = _PROJECT_ROOT / "data" / "expenses.json"
_EXPORTS_DIR = _PROJECT_ROOT / "exports"

# ── UI helpers ────────────────────────────────────────────────────────────────

def clear_screen() -> None:
    """Clear the terminal screen cross-platform."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str = "PYTHON EXPENSE TRACKER") -> None:
    """Print the application header banner."""
    print("\n" + "=" * 44)
    print(f"       {title}")
    print("=" * 44)


def print_success(message: str) -> None:
    print(f"\n  ✓  {message}")


def print_error(message: str) -> None:
    print(f"\n  ✗  Error: {message}")


def print_info(message: str) -> None:
    print(f"\n  ℹ  {message}")


def pause() -> None:
    """Wait for the user to press Enter before continuing."""
    input("\n  Press Enter to continue...")


def prompt(label: str, required: bool = True) -> str:
    """
    Read a non-empty string from stdin.
    If 'required' is True, re-prompt until a non-blank value is given.
    """
    while True:
        value = input(f"  {label}: ").strip()
        if value:
            return value
        if not required:
            return ""
        print("  This field is required. Please enter a value.")


def prompt_float(label: str) -> float | None:
    """Read a positive float from stdin, returning None on invalid input."""
    raw = input(f"  {label}: ").strip()
    try:
        value = float(raw)
        if value <= 0:
            print_error("Amount must be greater than zero.")
            return None
        return value
    except ValueError:
        print_error(f"'{raw}' is not a valid number.")
        return None


def prompt_int(label: str) -> int | None:
    """Read a positive integer from stdin, returning None on invalid input."""
    raw = input(f"  {label}: ").strip()
    try:
        value = int(raw)
        if value <= 0:
            print_error("ID must be a positive integer.")
            return None
        return value
    except ValueError:
        print_error(f"'{raw}' is not a valid integer.")
        return None


# ── Expense display ───────────────────────────────────────────────────────────

def _divider() -> str:
    return "  " + "-" * 72


def print_expense_row(expense: Expense) -> None:
    """Print a single expense as a formatted table row."""
    note_preview = f"  Note: {expense.note}" if expense.note else ""
    print(
        f"  [{expense.id:>4}]  {expense.date}  "
        f"{expense.title:<22}  ${expense.amount:>8,.2f}  "
        f"[{expense.category}]"
        f"{note_preview}"
    )


def print_expenses_table(expenses: list[Expense], heading: str = "Expenses") -> None:
    """Print a full table of expenses with a heading and footer total."""
    print(f"\n  {'─'*3} {heading} {'─'*(40 - len(heading))}")
    if not expenses:
        print("  No expenses found.")
        return

    print(f"  {'ID':>4}  {'Date':<10}  {'Title':<22}  {'Amount':>10}  Category")
    print(_divider())
    for expense in expenses:
        print_expense_row(expense)
    print(_divider())
    total = round(sum(e.amount for e in expenses), 2)
    print(f"  {'':>4}  {'':10}  {'TOTAL':<22}  ${total:>8,.2f}")
    print()


# ── Menu handlers ─────────────────────────────────────────────────────────────

def handle_add_expense(manager: ExpenseManager) -> None:
    """Collect expense details from the user and add it to the tracker."""
    print_header("ADD EXPENSE")

    title = prompt("Title")
    amount = prompt_float("Amount ($)")
    if amount is None:
        return

    category = prompt("Category (e.g. Food, Travel, Bills)")
    date_input = input("  Date (YYYY-MM-DD, leave blank for today): ").strip()

    # Allow blank date — the manager will default to today
    expense_date: str | None = date_input if date_input else None

    note = prompt("Note (optional)", required=False)

    try:
        expense = manager.add_expense(
            title=title,
            amount=amount,
            category=category,
            expense_date=expense_date,
            note=note,
        )
        print_success(
            f"Expense added → ID: {expense.id} | {expense.title} | "
            f"${expense.amount:,.2f} | {expense.category} | {expense.date}"
        )
    except (ValidationError, DuplicateExpenseError) as exc:
        print_error(str(exc))


def handle_view_all(manager: ExpenseManager) -> None:
    """Display all expenses sorted by date (newest first)."""
    print_header("ALL EXPENSES")
    expenses = manager.get_all_expenses(sort_by="date", reverse=True)
    print_expenses_table(expenses, heading="All Expenses")


def handle_delete_expense(manager: ExpenseManager) -> None:
    """Prompt for an ID and delete the matching expense."""
    print_header("DELETE EXPENSE")

    # Show current expenses so the user can pick an ID
    expenses = manager.get_all_expenses(sort_by="id", reverse=False)
    print_expenses_table(expenses, heading="Current Expenses")

    expense_id = prompt_int("Enter ID to delete")
    if expense_id is None:
        return

    confirm = input(f"  Confirm delete ID {expense_id}? (y/N): ").strip().lower()
    if confirm != "y":
        print_info("Deletion cancelled.")
        return

    try:
        removed = manager.delete_expense(expense_id)
        print_success(f"Deleted: [{removed.id}] {removed.title} — ${removed.amount:,.2f}")
    except ExpenseNotFoundError as exc:
        print_error(str(exc))


def handle_search(manager: ExpenseManager) -> None:
    """Search expenses by keyword in title or note."""
    print_header("SEARCH EXPENSES")
    query = prompt("Search keyword")
    results = manager.search_expenses(query)
    print_expenses_table(results, heading=f"Results for '{query}'")
    if not results:
        print_info("No matching expenses found.")


def handle_filter_by_category(manager: ExpenseManager) -> None:
    """Show all unique categories and filter expenses by user choice."""
    print_header("FILTER BY CATEGORY")

    categories = sorted(manager.get_categories())
    if not categories:
        print_info("No expenses recorded yet.")
        return

    print("\n  Available categories:")
    for idx, cat in enumerate(categories, start=1):
        print(f"    {idx}. {cat}")

    category = prompt("\n  Enter category name")
    results = manager.filter_by_category(category)
    print_expenses_table(results, heading=f"Category: {category}")
    if not results:
        print_info(f"No expenses in category '{category}'.")


def handle_filter_by_month(manager: ExpenseManager) -> None:
    """Filter expenses by a YYYY-MM month string."""
    print_header("FILTER BY MONTH")
    month_str = prompt("Enter month (YYYY-MM, e.g. 2026-11)")
    try:
        results = manager.filter_by_month(month_str)
        print_expenses_table(results, heading=f"Month: {month_str}")
        if not results:
            print_info(f"No expenses found for {month_str}.")
    except ValidationError as exc:
        print_error(str(exc))


def handle_reports(manager: ExpenseManager) -> None:
    """Display the full expense report."""
    print_header("EXPENSE REPORTS")
    printer = ReportPrinter()
    printer.print_full_report(manager.expenses)


def handle_export_csv(manager: ExpenseManager) -> None:
    """Export all expenses to a CSV file inside the exports directory."""
    print_header("EXPORT TO CSV")
    exporter = CSVExporter(exports_dir=_EXPORTS_DIR)
    try:
        output_path = exporter.export(manager.expenses)
        print_success(f"CSV exported successfully → {output_path}")
    except StorageError as exc:
        print_error(str(exc))


def handle_quiz() -> None:
    """Launch the Python knowledge quiz."""
    quiz = Quiz(num_questions=10)
    quiz.run()


# ── Main menu ────────────────────────────────────────────────────────────────

MENU_OPTIONS: tuple[tuple[str, str], ...] = (
    ("1", "Add Expense"),
    ("2", "View All Expenses"),
    ("3", "Delete Expense"),
    ("4", "Search Expense"),
    ("5", "Filter by Category"),
    ("6", "Filter by Month"),
    ("7", "View Expense Reports"),
    ("8", "Export to CSV"),
    ("9", "Python Knowledge Quiz"),
    ("0", "Exit"),
)


def print_menu(total_expenses: int, grand_total: float) -> None:
    """Render the main application menu."""
    clear_screen()
    print("\n" + "=" * 44)
    print("       PYTHON EXPENSE TRACKER")
    print("=" * 44)
    print(f"  Expenses tracked : {total_expenses}")
    print(f"  Total spent      : ${grand_total:,.2f}")
    print("─" * 44)
    for key, label in MENU_OPTIONS:
        print(f"  {key}.  {label}")
    print("=" * 44)


def run_menu(manager: ExpenseManager) -> None:
    """
    Main event loop — display the menu and dispatch to handlers.

    Uses a dict of lambdas (dispatch table) to route menu choices,
    demonstrating lambda functions and dictionary usage.
    """
    # Dispatch table: key → handler callable
    dispatch: dict[str, object] = {
        "1": lambda: handle_add_expense(manager),
        "2": lambda: handle_view_all(manager),
        "3": lambda: handle_delete_expense(manager),
        "4": lambda: handle_search(manager),
        "5": lambda: handle_filter_by_category(manager),
        "6": lambda: handle_filter_by_month(manager),
        "7": lambda: handle_reports(manager),
        "8": lambda: handle_export_csv(manager),
        "9": lambda: handle_quiz(),
        "0": None,  # Exit sentinel
    }

    while True:
        print_menu(
            total_expenses=len(manager),
            grand_total=manager.total_expenses(),
        )
        choice = input("\n  Enter your choice: ").strip()

        if choice == "0":
            print("\n  Goodbye! Keep tracking your expenses. 👋\n")
            break

        handler = dispatch.get(choice)
        if handler is None and choice != "0":
            print_error(f"'{choice}' is not a valid option. Please choose 0–9.")
        elif callable(handler):
            try:
                handler()  # type: ignore[call-arg]
            except KeyboardInterrupt:
                print_info("Action cancelled.")
            except ExpenseTrackerError as exc:
                print_error(str(exc))
            finally:
                pause()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Bootstrap the application:
    1. Initialise JSON storage.
    2. Load existing expenses.
    3. Start the interactive menu loop.
    """
    try:
        storage = JsonStorage(_DATA_FILE)
        manager = ExpenseManager(storage)

        # Surface any loading warnings (e.g. corrupted records)
        if hasattr(storage, "last_warning") and storage.last_warning:
            print_error(storage.last_warning)
            pause()

    except StorageError as exc:
        print(f"\n  FATAL: Could not initialise storage — {exc}\n")
        sys.exit(1)

    try:
        run_menu(manager)
    except KeyboardInterrupt:
        print("\n\n  Application interrupted. Goodbye!\n")


if __name__ == "__main__":
    main()
