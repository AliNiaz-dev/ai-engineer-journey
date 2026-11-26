"""
Pytest test suite for the Expense Tracker CLI.

Tests are fully isolated — they never touch the real expenses.json.
Every test that needs storage uses InMemoryStorage.
Tests that need a real file use the tmp_path pytest fixture (auto-cleaned).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from expense_tracker.exceptions import (
    DuplicateExpenseError,
    ExpenseNotFoundError,
    ValidationError,
)
from expense_tracker.exporter import CSVExporter
from expense_tracker.manager import ExpenseManager
from expense_tracker.models import Expense, validate_date, validate_month
from expense_tracker.reports import ReportPrinter, _category_totals, _monthly_totals
from expense_tracker.storage import InMemoryStorage, JsonStorage


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_manager(*expenses: Expense) -> ExpenseManager:
    """Return an ExpenseManager backed by in-memory storage, optionally pre-loaded."""
    storage = InMemoryStorage(list(expenses))
    return ExpenseManager(storage)


def sample_expense(
    expense_id: int = 1,
    title: str = "Coffee",
    amount: float = 4.50,
    category: str = "Food",
    date: str = "2026-11-01",
    note: str = "",
) -> Expense:
    """Factory helper for creating test Expense objects."""
    return Expense(
        id=expense_id,
        title=title,
        amount=amount,
        category=category,
        date=date,
        note=note,
    )


# ── Expense model validation ──────────────────────────────────────────────────

class TestExpenseValidation:
    def test_valid_expense_created_correctly(self):
        exp = sample_expense()
        assert exp.id == 1
        assert exp.title == "Coffee"
        assert exp.amount == 4.50
        assert exp.category == "Food"
        assert exp.date == "2026-11-01"

    def test_amount_rounded_to_two_decimals(self):
        exp = sample_expense(amount=4.9999)
        assert exp.amount == 5.0

    def test_amount_zero_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(amount=0)

    def test_amount_negative_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(amount=-10)

    def test_non_numeric_amount_raises_validation_error(self):
        with pytest.raises(ValidationError):
            Expense(id=1, title="X", amount="free", category="Food", date="2026-01-01")  # type: ignore

    def test_empty_title_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(title="")

    def test_whitespace_only_title_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(title="   ")

    def test_empty_category_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(category="")

    def test_invalid_date_format_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(date="26-11-2026")

    def test_nonsense_date_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(date="2026-99-99")

    def test_zero_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(expense_id=0)

    def test_negative_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            sample_expense(expense_id=-5)

    def test_title_stripped_of_whitespace(self):
        exp = sample_expense(title="  Groceries  ")
        assert exp.title == "Groceries"

    def test_note_defaults_to_empty_string(self):
        exp = sample_expense()
        assert exp.note == ""

    def test_to_dict_round_trip(self):
        exp = sample_expense(expense_id=7, note="lunch")
        d = exp.to_dict()
        restored = Expense.from_dict(d)
        assert restored.id == exp.id
        assert restored.title == exp.title
        assert restored.amount == exp.amount
        assert restored.note == exp.note

    def test_from_dict_missing_required_key_raises_validation_error(self):
        with pytest.raises(ValidationError):
            Expense.from_dict({"title": "X", "amount": 10, "category": "Food", "date": "2026-01-01"})


# ── Date / Month validation helpers ──────────────────────────────────────────

class TestDateValidation:
    def test_valid_date_returns_cleaned(self):
        assert validate_date("2026-11-26") == "2026-11-26"

    def test_valid_date_strips_spaces(self):
        assert validate_date("  2026-11-01  ") == "2026-11-01"

    def test_invalid_date_format_raises(self):
        with pytest.raises(ValidationError):
            validate_date("11/26/2026")

    def test_invalid_calendar_date_raises(self):
        with pytest.raises(ValidationError):
            validate_date("2026-02-30")

    def test_valid_month_returns_cleaned(self):
        assert validate_month("2026-11") == "2026-11"

    def test_invalid_month_format_raises(self):
        with pytest.raises(ValidationError):
            validate_month("11-2026")

    def test_invalid_calendar_month_raises(self):
        with pytest.raises(ValidationError):
            validate_month("2026-13")


# ── Adding expenses ───────────────────────────────────────────────────────────

class TestAddExpense:
    def test_add_single_expense(self):
        manager = make_manager()
        exp = manager.add_expense("Coffee", 4.50, "Food", "2026-11-01")
        assert exp.id == 1
        assert len(manager) == 1

    def test_add_multiple_expenses_auto_increments_id(self):
        manager = make_manager()
        e1 = manager.add_expense("Coffee", 4.50, "Food", "2026-11-01")
        e2 = manager.add_expense("Bus", 2.00, "Travel", "2026-11-02")
        assert e2.id == e1.id + 1

    def test_add_expense_persists_to_storage(self):
        storage = InMemoryStorage()
        manager = ExpenseManager(storage)
        manager.add_expense("Test", 10.0, "Misc", "2026-11-05")
        # Reload from same storage to verify persistence
        reloaded = ExpenseManager(storage)
        assert len(reloaded) == 1

    def test_add_expense_defaults_date_to_today(self):
        from datetime import date
        manager = make_manager()
        exp = manager.add_expense("No date", 5.0, "Misc")
        assert exp.date == date.today().isoformat()

    def test_add_expense_with_explicit_id(self):
        manager = make_manager()
        exp = manager.add_expense("X", 1.0, "Food", "2026-01-01", expense_id=42)
        assert exp.id == 42

    def test_add_duplicate_id_raises_duplicate_error(self):
        existing = sample_expense(expense_id=5)
        manager = make_manager(existing)
        with pytest.raises(DuplicateExpenseError):
            manager.add_expense("Y", 2.0, "Food", "2026-01-01", expense_id=5)

    def test_add_zero_amount_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.add_expense("Z", 0.0, "Food", "2026-01-01")

    def test_add_negative_amount_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.add_expense("Z", -5.0, "Food", "2026-01-01")

    def test_add_empty_title_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.add_expense("", 5.0, "Food", "2026-01-01")

    def test_add_empty_category_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.add_expense("Coffee", 5.0, "", "2026-01-01")

    def test_add_bad_date_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.add_expense("Coffee", 5.0, "Food", "not-a-date")


# ── Deleting expenses ─────────────────────────────────────────────────────────

class TestDeleteExpense:
    def test_delete_existing_expense(self):
        exp = sample_expense(expense_id=1)
        manager = make_manager(exp)
        removed = manager.delete_expense(1)
        assert removed.id == 1
        assert len(manager) == 0

    def test_delete_reduces_count_by_one(self):
        manager = make_manager(
            sample_expense(expense_id=1),
            sample_expense(expense_id=2, title="Bus"),
        )
        manager.delete_expense(1)
        assert len(manager) == 1

    def test_delete_nonexistent_id_raises_not_found(self):
        manager = make_manager()
        with pytest.raises(ExpenseNotFoundError):
            manager.delete_expense(999)

    def test_delete_persists_to_storage(self):
        storage = InMemoryStorage([sample_expense(expense_id=1)])
        manager = ExpenseManager(storage)
        manager.delete_expense(1)
        reloaded = ExpenseManager(storage)
        assert len(reloaded) == 0

    def test_delete_correct_expense_when_multiple_present(self):
        e1 = sample_expense(expense_id=1, title="Coffee")
        e2 = sample_expense(expense_id=2, title="Bus")
        manager = make_manager(e1, e2)
        manager.delete_expense(1)
        remaining = manager.expenses
        assert len(remaining) == 1
        assert remaining[0].title == "Bus"


# ── Searching expenses ────────────────────────────────────────────────────────

class TestSearchExpense:
    def test_search_matches_title_case_insensitive(self):
        manager = make_manager(sample_expense(title="Morning Coffee"))
        results = manager.search_expenses("coffee")
        assert len(results) == 1

    def test_search_matches_note(self):
        exp = Expense(id=1, title="Food", amount=10, category="Food",
                      date="2026-01-01", note="bought lunch")
        manager = make_manager(exp)
        results = manager.search_expenses("lunch")
        assert len(results) == 1

    def test_search_returns_empty_for_no_match(self):
        manager = make_manager(sample_expense())
        results = manager.search_expenses("xyz_nonexistent")
        assert results == []

    def test_search_empty_query_returns_empty(self):
        manager = make_manager(sample_expense())
        results = manager.search_expenses("")
        assert results == []

    def test_search_returns_multiple_matches(self):
        manager = make_manager(
            sample_expense(expense_id=1, title="Morning Coffee"),
            sample_expense(expense_id=2, title="Afternoon Coffee"),
            sample_expense(expense_id=3, title="Tea"),
        )
        results = manager.search_expenses("coffee")
        assert len(results) == 2


# ── Filtering by category ─────────────────────────────────────────────────────

class TestFilterByCategory:
    def test_filter_returns_matching_category(self):
        manager = make_manager(
            sample_expense(expense_id=1, category="Food"),
            sample_expense(expense_id=2, category="Travel"),
        )
        results = manager.filter_by_category("Food")
        assert all(e.category == "Food" for e in results)
        assert len(results) == 1

    def test_filter_case_insensitive(self):
        manager = make_manager(sample_expense(category="Food"))
        results = manager.filter_by_category("FOOD")
        assert len(results) == 1

    def test_filter_returns_empty_for_unknown_category(self):
        manager = make_manager(sample_expense(category="Food"))
        results = manager.filter_by_category("Entertainment")
        assert results == []

    def test_filter_empty_string_returns_empty(self):
        manager = make_manager(sample_expense())
        assert manager.filter_by_category("") == []

    def test_filter_multiple_expenses_same_category(self):
        manager = make_manager(
            sample_expense(expense_id=1, category="Food"),
            sample_expense(expense_id=2, category="Food", title="Pizza"),
            sample_expense(expense_id=3, category="Travel"),
        )
        results = manager.filter_by_category("Food")
        assert len(results) == 2


# ── Filtering by month ────────────────────────────────────────────────────────

class TestFilterByMonth:
    def test_filter_returns_expenses_in_month(self):
        manager = make_manager(
            sample_expense(expense_id=1, date="2026-11-01"),
            sample_expense(expense_id=2, date="2026-11-30"),
            sample_expense(expense_id=3, date="2026-10-15"),
        )
        results = manager.filter_by_month("2026-11")
        assert len(results) == 2

    def test_filter_returns_empty_for_no_expenses_in_month(self):
        manager = make_manager(sample_expense(date="2026-11-01"))
        results = manager.filter_by_month("2026-01")
        assert results == []

    def test_filter_invalid_month_format_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.filter_by_month("11-2026")

    def test_filter_invalid_month_value_raises_validation_error(self):
        manager = make_manager()
        with pytest.raises(ValidationError):
            manager.filter_by_month("2026-13")


# ── Total calculation ─────────────────────────────────────────────────────────

class TestTotalExpenses:
    def test_total_is_zero_when_no_expenses(self):
        manager = make_manager()
        assert manager.total_expenses() == 0.0

    def test_total_sums_all_amounts(self):
        manager = make_manager(
            sample_expense(expense_id=1, amount=10.00),
            sample_expense(expense_id=2, amount=5.50),
            sample_expense(expense_id=3, amount=4.50),
        )
        assert manager.total_expenses() == 20.00

    def test_total_rounds_to_two_decimals(self):
        manager = make_manager(
            sample_expense(expense_id=1, amount=0.1),
            sample_expense(expense_id=2, amount=0.2),
        )
        # Avoids floating-point pitfalls
        assert abs(manager.total_expenses() - 0.3) < 0.001


# ── Reports ───────────────────────────────────────────────────────────────────

class TestReports:
    def _expenses(self) -> list[Expense]:
        return [
            Expense(id=1, title="Coffee", amount=4.50, category="Food", date="2026-11-01"),
            Expense(id=2, title="Bus", amount=2.00, category="Travel", date="2026-11-02"),
            Expense(id=3, title="Dinner", amount=18.00, category="Food", date="2026-10-15"),
        ]

    def test_category_totals_correct(self):
        totals = _category_totals(self._expenses())
        assert totals["Food"] == pytest.approx(22.50)
        assert totals["Travel"] == pytest.approx(2.00)

    def test_monthly_totals_correct(self):
        totals = _monthly_totals(self._expenses())
        assert totals["2026-10"] == pytest.approx(18.00)
        assert totals["2026-11"] == pytest.approx(6.50)

    def test_report_printer_no_crash_on_empty(self, capsys):
        printer = ReportPrinter()
        printer.print_full_report([])
        captured = capsys.readouterr()
        assert "No expenses" in captured.out

    def test_report_printer_shows_total(self, capsys):
        printer = ReportPrinter()
        printer.print_full_report(self._expenses())
        captured = capsys.readouterr()
        assert "24.50" in captured.out

    def test_get_categories_returns_set(self):
        manager = make_manager(
            sample_expense(expense_id=1, category="Food"),
            sample_expense(expense_id=2, category="Travel"),
            sample_expense(expense_id=3, category="Food"),
        )
        cats = manager.get_categories()
        assert isinstance(cats, set)
        assert cats == {"Food", "Travel"}


# ── JSON Storage ──────────────────────────────────────────────────────────────

class TestJsonStorage:
    def test_saves_and_loads_expenses(self, tmp_path: Path):
        json_file = tmp_path / "expenses.json"
        storage = JsonStorage(json_file)
        exp = sample_expense()
        storage.save([exp])
        loaded = storage.load()
        assert len(loaded) == 1
        assert loaded[0].id == exp.id

    def test_load_missing_file_returns_empty_list(self, tmp_path: Path):
        storage = JsonStorage(tmp_path / "nonexistent.json")
        assert storage.load() == []

    def test_load_empty_file_returns_empty_list(self, tmp_path: Path):
        json_file = tmp_path / "empty.json"
        json_file.write_text("", encoding="utf-8")
        storage = JsonStorage(json_file)
        assert storage.load() == []

    def test_load_corrupted_json_returns_empty_and_warns(self, tmp_path: Path):
        json_file = tmp_path / "bad.json"
        json_file.write_text("{{not valid JSON!!", encoding="utf-8")
        storage = JsonStorage(json_file)
        result = storage.load()
        assert result == []
        assert storage.last_warning is not None

    def test_load_non_list_json_returns_empty_and_warns(self, tmp_path: Path):
        json_file = tmp_path / "wrong.json"
        json_file.write_text('{"key": "value"}', encoding="utf-8")
        storage = JsonStorage(json_file)
        result = storage.load()
        assert result == []
        assert storage.last_warning is not None

    def test_save_overwrites_previous_data(self, tmp_path: Path):
        json_file = tmp_path / "expenses.json"
        storage = JsonStorage(json_file)
        storage.save([sample_expense(expense_id=1)])
        storage.save([sample_expense(expense_id=2, title="New")])
        loaded = storage.load()
        assert len(loaded) == 1
        assert loaded[0].id == 2

    def test_data_persists_across_storage_instances(self, tmp_path: Path):
        json_file = tmp_path / "expenses.json"
        storage1 = JsonStorage(json_file)
        storage1.save([sample_expense(expense_id=1, title="Persistent")])
        storage2 = JsonStorage(json_file)
        loaded = storage2.load()
        assert loaded[0].title == "Persistent"


# ── CSV Exporter ──────────────────────────────────────────────────────────────

class TestCSVExporter:
    def test_export_creates_csv_file(self, tmp_path: Path):
        exporter = CSVExporter(exports_dir=tmp_path)
        expenses = [sample_expense()]
        path = exporter.export(expenses)
        assert path.exists()
        assert path.suffix == ".csv"

    def test_export_csv_contains_headers(self, tmp_path: Path):
        exporter = CSVExporter(exports_dir=tmp_path)
        path = exporter.export([sample_expense()])
        content = path.read_text(encoding="utf-8")
        assert "Title" in content
        assert "Amount" in content

    def test_export_csv_contains_expense_data(self, tmp_path: Path):
        exporter = CSVExporter(exports_dir=tmp_path)
        exp = sample_expense(title="Unit Test Expense", amount=99.99)
        path = exporter.export([exp])
        content = path.read_text(encoding="utf-8")
        assert "Unit Test Expense" in content
        assert "99.99" in content

    def test_export_empty_list_raises_storage_error(self, tmp_path: Path):
        from expense_tracker.exceptions import StorageError
        exporter = CSVExporter(exports_dir=tmp_path)
        with pytest.raises(StorageError):
            exporter.export([])

    def test_export_multiple_expenses(self, tmp_path: Path):
        exporter = CSVExporter(exports_dir=tmp_path)
        expenses = [
            sample_expense(expense_id=1, title="A"),
            sample_expense(expense_id=2, title="B"),
        ]
        path = exporter.export(expenses)
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        # 1 header + 2 data rows
        assert len(lines) == 3


# ── Manager iterator / sorting ────────────────────────────────────────────────

class TestManagerIteratorAndSorting:
    def test_iter_expenses_yields_all(self):
        manager = make_manager(
            sample_expense(expense_id=1),
            sample_expense(expense_id=2, title="Bus"),
        )
        yielded = list(manager.iter_expenses())
        assert len(yielded) == 2

    def test_get_all_sorted_by_amount(self):
        manager = make_manager(
            sample_expense(expense_id=1, amount=50.0),
            sample_expense(expense_id=2, amount=10.0),
            sample_expense(expense_id=3, amount=30.0),
        )
        sorted_expenses = manager.get_all_expenses(sort_by="amount", reverse=False)
        amounts = [e.amount for e in sorted_expenses]
        assert amounts == sorted(amounts)

    def test_get_all_invalid_sort_key_raises(self):
        manager = make_manager(sample_expense())
        with pytest.raises(ValidationError):
            manager.get_all_expenses(sort_by="nonexistent_field")

    def test_len_manager_returns_expense_count(self):
        manager = make_manager(
            sample_expense(expense_id=1),
            sample_expense(expense_id=2, title="Bus"),
        )
        assert len(manager) == 2
