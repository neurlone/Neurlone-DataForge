# Neurlone DataForge

A Python command-line tool for cleaning and validating CSV and Excel tables, with before-and-after quality reports.

## Features

- Read CSV, XLSX, and legacy XLS files.
- Report row/column counts, missing cells, duplicate rows, and missing values by column.
- Trim text whitespace and treat whitespace-only cells as missing.
- Keep, drop, or fill missing values.
- Keep duplicates, keep the first/last occurrence, or remove all copies of duplicated rows.
- Export cleaned data to a new CSV or XLSX file.
- Optionally write a JSON processing report.
- Automated tests using Python's built-in `unittest`.

## Requirements

Python 3.13 or 3.14 is recommended. Install dependencies in a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Usage

Run from the project root:

```powershell
python main.py "data\customers.csv"
```

Choose an output path and cleaning policies:

```powershell
python main.py "data\customers.csv" --output "data\customers_cleaned.csv" --missing drop --duplicates first
```

Fill missing values and create a JSON report:

```powershell
python main.py "data\sales.xlsx" --missing fill --fill-value "Unknown" --duplicates last --report "data\sales_report.json"
```

Choose an Excel sheet by name or zero-based index:

```powershell
python main.py "data\sales.xlsx" --sheet "January" --output "data\january_cleaned.xlsx"
```

Disable text trimming:

```powershell
python main.py "data\customers.csv" --no-trim
```

See all options:

```powershell
python main.py --help
```

## Cleaning options

| Option | Behavior |
|---|---|
| `--missing keep` | Preserve rows with missing values (default) |
| `--missing drop` | Remove rows containing at least one missing cell |
| `--missing fill` | Replace missing cells with `--fill-value` |
| `--duplicates keep` | Preserve all duplicate rows |
| `--duplicates first` | Keep the first copy (default) |
| `--duplicates last` | Keep the last copy |
| `--duplicates all` | Remove every row that has a duplicate |
| `--no-trim` | Skip text whitespace cleanup |

DataForge never intentionally writes cleaned data over the input file. The default output name adds `_cleaned` to the input filename. CSV and XLSX are supported output formats; XLS is read-only.

## Run tests

```powershell
python -m unittest discover -v
```

## Scope and limitations

Version 1.0 processes one table at a time. For Excel files, it reads the selected worksheet (the first sheet by default), not every worksheet in a workbook. It exports cell data, not workbook formatting, formulas, charts, or macros. Review the generated output and report before using cleaned data in critical workflows.
