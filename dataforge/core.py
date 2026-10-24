"""Core data loading, cleaning, and reporting logic."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

SUPPORTED_INPUTS = {".csv", ".xlsx", ".xls"}
SUPPORTED_OUTPUTS = {".csv", ".xlsx"}


class DataForgeError(Exception):
    """Base exception for expected DataForge errors."""


def validate_input_path(path: str | Path) -> Path:
    source = Path(path).expanduser()

    if not source.exists():
        raise DataForgeError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise DataForgeError(f"Input path is not a file: {source}")
    if source.suffix.lower() not in SUPPORTED_INPUTS:
        supported = ", ".join(sorted(SUPPORTED_INPUTS))
        raise DataForgeError(f"Unsupported input format '{source.suffix}'. Use: {supported}")
    if source.stat().st_size == 0:
        raise DataForgeError("Input file is empty.")
    return source.resolve()


def load_data(path: str | Path, sheet: str | int = 0) -> pd.DataFrame:
    source = validate_input_path(path)

    try:
        if source.suffix.lower() == ".csv":
            # utf-8-sig handles regular UTF-8 and CSV files with a BOM.
            frame = pd.read_csv(source, encoding="utf-8-sig")
        else:
            engine = "xlrd" if source.suffix.lower() == ".xls" else "openpyxl"
            frame = pd.read_excel(source, sheet_name=sheet, engine=engine)
    except ImportError as exc:
        dependency = "xlrd" if source.suffix.lower() == ".xls" else "openpyxl"
        raise DataForgeError(
            f"Missing dependency '{dependency}'. Install project requirements."
        ) from exc
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError, OSError) as exc:
        raise DataForgeError(f"Could not read input file: {exc}") from exc
    except Exception as exc:
        # Excel engines can raise format-specific exceptions; present a concise CLI error.
        raise DataForgeError(f"Could not read input file: {exc}") from exc

    if frame.empty and len(frame.columns) == 0:
        raise DataForgeError("The file contains no tabular columns.")
    if len(frame.columns) == 0:
        raise DataForgeError("The file contains no columns.")
    if any(not str(column).strip() for column in frame.columns):
        raise DataForgeError("One or more column names are blank. Rename them and try again.")
    if not frame.columns.is_unique:
        raise DataForgeError("Column names must be unique.")
    return frame


def get_report(frame: pd.DataFrame) -> dict[str, Any]:
    """Return compact, JSON-serializable summary statistics."""
    return {
        "rows": len(frame),
"columns": len(frame.columns),
"missing_cells": frame.isna().sum().sum(),
        "duplicate_rows": int(frame.duplicated().sum()),
        "missing_by_column": {
            str(column): int(count)
            for column, count in frame.isna().sum().items()
        },
    }


def clean_data(
    frame: pd.DataFrame,
    *,
    missing: str = "keep",
    fill_value: str = "",
    duplicates: str = "first",
    trim_text: bool = True,
) -> pd.DataFrame:
    """Clean a copy of a DataFrame according to explicit user choices."""
    if missing not in {"keep", "drop", "fill"}:
        raise DataForgeError("Missing-value mode must be keep, drop, or fill.")
    if duplicates not in {"keep", "first", "last", "all"}:
        raise DataForgeError("Duplicate mode must be keep, first, last, or all.")

    cleaned = frame.copy(deep=True)

    if trim_text:
        for column in cleaned.select_dtypes(include=["object", "string"]).columns:
            values = cleaned[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            # Whitespace-only strings become missing values for consistent reporting.
            cleaned[column] = values.map(
                lambda value: pd.NA if isinstance(value, str) and value == "" else value
            )

    if missing == "drop":
        cleaned = cleaned.dropna(axis=0, how="any")
    elif missing == "fill":
        cleaned = cleaned.fillna(fill_value)

    if duplicates == "first":
        cleaned = cleaned.drop_duplicates(keep="first")
    elif duplicates == "last":
        cleaned = cleaned.drop_duplicates(keep="last")
    elif duplicates == "all":
        cleaned = cleaned.loc[~cleaned.duplicated(keep=False)].copy()

    return cleaned.reset_index(drop=True)


def save_data(frame: pd.DataFrame, output_path: str | Path, input_path: str | Path) -> Path:
    """Save cleaned data without ever overwriting the source file."""
    destination = Path(output_path).expanduser()
    if destination.suffix.lower() not in SUPPORTED_OUTPUTS:
        raise DataForgeError("Output format must be .csv or .xlsx.")

    source = Path(input_path).expanduser().resolve()
    resolved_destination = destination.resolve()

    if source == resolved_destination:
        raise DataForgeError("Output path must differ from the original input file.")
    if destination.exists() and destination.is_dir():
        raise DataForgeError("Output path points to a directory.")
    if not destination.parent.exists():
        raise DataForgeError(f"Output directory does not exist: {destination.parent}")

    try:
        if destination.suffix.lower() == ".csv":
            frame.to_csv(destination, index=False, encoding="utf-8-sig")
        else:
            frame.to_excel(destination, index=False, engine="openpyxl")
    except (PermissionError, OSError, ValueError) as exc:
        raise DataForgeError(f"Could not save output file: {exc}") from exc

    return destination.resolve()
