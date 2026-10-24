"""Command-line interface for Neurlone DataForge."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dataforge.core import DataForgeError, clean_data, get_report, load_data, save_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dataforge",
        description="Clean CSV and Excel files and generate before/after reports.",
    )
    parser.add_argument("input", help="Input .csv, .xlsx, or .xls file")
    parser.add_argument(
        "-o", "--output",
        help="Output .csv or .xlsx path (default: <input>_cleaned with matching supported format)",
    )
    parser.add_argument(
        "--sheet", default="0",
        help="Excel sheet name or zero-based sheet index (default: 0)",
    )
    parser.add_argument(
        "--missing", choices=("keep", "drop", "fill"), default="keep",
        help="How to handle rows containing missing values (default: keep)",
    )
    parser.add_argument(
        "--fill-value", default="",
        help="Value used with --missing fill (default: empty string)",
    )
    parser.add_argument(
        "--duplicates", choices=("keep", "first", "last", "all"), default="first",
        help="Duplicate-row policy: keep, first, last, or all (default: first)",
    )
    parser.add_argument(
        "--no-trim", action="store_true",
        help="Do not trim text whitespace or convert whitespace-only text to missing values",
    )
    parser.add_argument(
        "--report",
        help="Optional path for a JSON before/after report",
    )
    return parser


def _parse_sheet(value: str) -> str | int:
    try:
        index = int(value)
        if index < 0:
            raise ValueError
        return index
    except ValueError:
        if value.strip():
            return value
        raise DataForgeError("Sheet must be a non-negative index or a non-empty name.")


def _default_output(input_path: str) -> Path:
    source = Path(input_path).expanduser()
    suffix = ".csv" if source.suffix.lower() == ".csv" else ".xlsx"
    return source.with_name(f"{source.stem}_cleaned{suffix}")


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        sheet = _parse_sheet(args.sheet)
        original = load_data(args.input, sheet=sheet)
        cleaned = clean_data(
            original,
            missing=args.missing,
            fill_value=args.fill_value,
            duplicates=args.duplicates,
            trim_text=not args.no_trim,
        )
        output_path = args.output or str(_default_output(args.input))
        saved_path = save_data(cleaned, output_path, args.input)

        report = {
            "input_file": str(Path(args.input).expanduser().resolve()),
            "output_file": str(saved_path),
            "settings": {
                "missing": args.missing,
                "fill_value": args.fill_value if args.missing == "fill" else None,
                "duplicates": args.duplicates,
                "trim_text": not args.no_trim,
                "sheet": sheet if Path(args.input).suffix.lower() in {".xlsx", ".xls"} else None,
            },
            "before": get_report(original),
            "after": get_report(cleaned),
        }

        if args.report:
            report_path = Path(args.report).expanduser()
            if report_path.resolve() in {
                Path(args.input).expanduser().resolve(),
                saved_path.resolve(),
            }:
                raise DataForgeError("Report path must differ from input and output paths.")
            if report_path.suffix.lower() != ".json":
                raise DataForgeError("Report file must use the .json extension.")
            if not report_path.parent.exists():
                raise DataForgeError(f"Report directory does not exist: {report_path.parent}")
            report_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"Report saved: {report_path.resolve()}")

        print("\nNeurlone DataForge — processing complete")
        print(f"Input:  {report['input_file']}")
        print(f"Output: {saved_path}")
        print("\nMetric              Before       After")
        print("-" * 42)
        for label, key in (
            ("Rows", "rows"),
            ("Columns", "columns"),
            ("Missing cells", "missing_cells"),
            ("Duplicate rows", "duplicate_rows"),
        ):
            print(f"{label:<20}{report['before'][key]:>8}{report['after'][key]:>13}")
        return 0

    except DataForgeError as exc:
        print(f"DataForge error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
