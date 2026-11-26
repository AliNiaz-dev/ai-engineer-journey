# 🐍 Python Expense Tracker CLI

A **complete, beginner-friendly** command-line application for tracking personal expenses, built entirely with Python's standard library. Designed to demonstrate core and intermediate Python concepts for anyone learning Python for a career in software or AI engineering.

---

## ✨ Features

| # | Feature |
|---|---------|
| 1 | **Add Expense** — record title, amount, category, date, and optional note |
| 2 | **View All Expenses** — sorted, tabular listing with running total |
| 3 | **Delete Expense** — remove an expense by its ID with confirmation |
| 4 | **Search Expenses** — keyword search across title and note |
| 5 | **Filter by Category** — view only expenses in a chosen category |
| 6 | **Filter by Month** — view expenses for any YYYY-MM period |
| 7 | **Expense Reports** — overview, category totals, monthly summary, highest/lowest |
| 8 | **Export to CSV** — timestamped CSV file saved in `exports/` |
| 9 | **Python Knowledge Quiz** — 10-question multiple-choice quiz with score & review |
| 10 | **Persistent JSON Storage** — expenses survive application restarts |

---

## 🛠️ Technologies

- **Language**: Python 3.10+
- **Standard library only** (main app): `json`, `csv`, `pathlib`, `datetime`, `dataclasses`, `collections`, `abc`, `re`, `random`, `shutil`, `os`, `sys`
- **Testing**: [pytest](https://docs.pytest.org/) ≥ 7.0

---

## 🧠 Python Concepts Demonstrated

| Concept | Where Used |
|---------|-----------|
| Variables & data types | Throughout all modules |
| Lists, dicts, sets, tuples | `manager.py`, `reports.py`, `main.py` |
| Conditions & loops | `main.py` menu loop, all filters |
| Functions & return values | Every module |
| Positional & keyword arguments | `add_expense()` in `manager.py` |
| **Lambda functions** | Dispatch table in `main.py`; sort keys in `manager.py` |
| **List & dict comprehensions** | `manager.py` search, filter, `reports.py` totals |
| **OOP — Classes & objects** | `Expense`, `ExpenseManager`, `JsonStorage`, `CSVExporter`, `Quiz` |
| **Encapsulation** | Private `_` attributes in `ExpenseManager`, `JsonStorage` |
| **Inheritance** | `JsonStorage`, `InMemoryStorage` inherit `BaseStorage` |
| **Polymorphism** | `load()` / `save()` behave differently per storage class |
| **Abstraction** | `BaseStorage` ABC with abstract methods |
| **Dataclasses** | `Expense`, `QuizQuestion`, `QuizResult` |
| **File handling** | `JsonStorage`, `CSVExporter` |
| **JSON handling** | `storage.py` |
| **CSV handling** | `exporter.py` |
| **Exception handling** | Try/except blocks throughout; custom exceptions in `exceptions.py` |
| **Custom exceptions** | `ValidationError`, `DuplicateExpenseError`, `ExpenseNotFoundError`, `StorageError` |
| **Modules & packages** | Full `src` layout with `__init__.py` |
| **Type hints** | Every function signature across all modules |
| **Iterators & generators** | `iter_report_lines()` generator in `reports.py`; `iter_expenses()` in `manager.py` |

---

## 📁 Project Structure

```
expense-tracker-cli/
│
├── src/
│   └── expense_tracker/
│       ├── __init__.py        # Package exports
│       ├── main.py            # CLI entry point & menu
│       ├── models.py          # Expense dataclass + validation
│       ├── manager.py         # Business logic (add/delete/filter/search)
│       ├── storage.py         # JSON + in-memory storage backends
│       ├── reports.py         # Report generation (generator-based)
│       ├── exporter.py        # CSV export
│       ├── exceptions.py      # Custom exception hierarchy
│       └── quiz.py            # Python knowledge quiz
│
├── tests/
│   └── test_manager.py        # Full pytest suite (60+ tests)
│
├── data/
│   └── expenses.json          # Persistent storage (auto-created)
│
├── exports/                   # CSV exports land here
│
├── README.md
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10 or later — check with `python --version`

### 1. Clone / download the project
```bash
git clone https://github.com/your-username/expense-tracker-cli.git
cd expense-tracker-cli
```

### 2. Create and activate a virtual environment *(recommended)*
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install in editable mode (includes pytest)
```bash
pip install -e ".[dev]"
```

---

## ▶️ Running the Application

```bash
# From the project root
python -m expense_tracker.main

# Or, after editable install
expense-tracker
```

The interactive menu appears:

```
============================================
       PYTHON EXPENSE TRACKER
============================================
  Expenses tracked : 3
  Total spent      : $45.50
--------------------------------------------
  1.  Add Expense
  2.  View All Expenses
  3.  Delete Expense
  4.  Search Expense
  5.  Filter by Category
  6.  Filter by Month
  7.  View Expense Reports
  8.  Export to CSV
  9.  Python Knowledge Quiz
  0.  Exit
============================================
```

---

## 🧪 Running Tests

```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run a specific test class:
```bash
pytest tests/test_manager.py::TestAddExpense -v
```

> Tests use **in-memory storage** and pytest's `tmp_path` fixture — your real `expenses.json` is never touched.

---

## 📋 Example Usage

### Add an expense
```
  Title: Morning Coffee
  Amount ($): 4.50
  Category: Food
  Date (YYYY-MM-DD, leave blank for today): 2026-11-26
  Note (optional): Oat milk latte

  ✓  Expense added → ID: 1 | Morning Coffee | $4.50 | Food | 2026-11-26
```

### View all expenses
```
  ─── All Expenses ─────────────────────────────────────
    ID  Date        Title                   Amount  Category
  ────────────────────────────────────────────────────────────────────────────
  [   1]  2026-11-26  Morning Coffee            $    4.50  [Food]
  [   2]  2026-11-25  Uber ride                 $   12.00  [Travel]
  ────────────────────────────────────────────────────────────────────────────
              TOTAL                             $   16.50
```

### Export to CSV
```
  ✓  CSV exported successfully → C:\...\exports\expenses_20261126_143022.csv
```

---

## 🚀 Future Improvements

- [ ] Budget limits per category with overspend alerts
- [ ] Recurring expense tracking
- [ ] Currency conversion support
- [ ] Rich terminal UI using the `rich` library
- [ ] SQLite database backend option
- [ ] Web dashboard using Flask or FastAPI
- [ ] Expense import from bank CSV statements
- [ ] Multi-user / profile support

---

## 📄 License

MIT — free to use, modify, and distribute.
