"""Report generation for expense summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Generator

from expense_tracker.exceptions import ExpenseTrackerError
from expense_tracker.models import Expense


def _category_totals(expenses: list[Expense]) -> dict[str, float]:
    """Return a dict mapping each category to its total amount."""
    totals: dict[str, float] = defaultdict(float)
    for expense in expenses:
        totals[expense.category] += expense.amount
    return {cat: round(total, 2) for cat, total in sorted(totals.items())}


def _monthly_totals(expenses: list[Expense]) -> dict[str, float]:
    """Return a dict mapping YYYY-MM to total amount for that month."""
    totals: dict[str, float] = defaultdict(float)
    for expense in expenses:
        month = expense.date[:7]  # YYYY-MM
        totals[month] += expense.amount
    return {month: round(total, 2) for month, total in sorted(totals.items())}


def iter_report_lines(expenses: list[Expense]) -> Generator[str, None, None]:
    """
    Yield lines of the full expense report one at a time.

    This is a generator — a good demonstration of lazy iteration for
    potentially large datasets without building the entire string in memory.
    """
    if not expenses:
        yield "  No expenses recorded yet."
        return

    total = round(sum(e.amount for e in expenses), 2)
    highest = max(expenses, key=lambda e: e.amount)
    lowest = min(expenses, key=lambda e: e.amount)

    # ── Overview ──────────────────────────────────────────────────────────
    yield ""
    yield "  ─── OVERVIEW ────────────────────────────────────"
    yield f"  Total expenses   : {len(expenses)}"
    yield f"  Grand total      : ${total:,.2f}"
    yield f"  Highest expense  : {highest.title} — ${highest.amount:,.2f} ({highest.date})"
    yield f"  Lowest expense   : {lowest.title} — ${lowest.amount:,.2f} ({lowest.date})"

    # ── Category-wise totals ──────────────────────────────────────────────
    yield ""
    yield "  ─── CATEGORY TOTALS ─────────────────────────────"
    for category, cat_total in _category_totals(expenses).items():
        percentage = (cat_total / total * 100) if total else 0
        yield f"  {category:<20} ${cat_total:>10,.2f}   ({percentage:.1f}%)"

    # ── Monthly summary ───────────────────────────────────────────────────
    yield ""
    yield "  ─── MONTHLY SUMMARY ─────────────────────────────"
    for month, mon_total in _monthly_totals(expenses).items():
        yield f"  {month}          ${mon_total:>10,.2f}"

    yield ""


class ReportPrinter:
    """
    Encapsulates printing expense reports to stdout.

    Demonstrates:
    - Encapsulation: internal helper methods are prefixed with _
    - Polymorphism: could be subclassed for file-based, HTML, etc. output
    """

    def print_full_report(self, expenses: list[Expense]) -> None:
        """Print the complete expense report to the terminal."""
        for line in iter_report_lines(expenses):
            print(line)

    def print_category_totals(self, expenses: list[Expense]) -> None:
        """Print a compact category breakdown."""
        if not expenses:
            print("  No expenses to summarise.")
            return
        total = round(sum(e.amount for e in expenses), 2)
        print()
        for category, cat_total in _category_totals(expenses).items():
            pct = (cat_total / total * 100) if total else 0
            print(f"  {category:<20} ${cat_total:>10,.2f}  ({pct:.1f}%)")
        print()
