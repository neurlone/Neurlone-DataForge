
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from dataforge.core import (
    DataForgeError,
    clean_data,
    get_report,
    load_data,
    save_data,
    validate_input_path,
)


class TestDataForge(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)

    def test_report_counts_rows_missing_and_duplicates(self):
        frame = pd.DataFrame({
            "name": ["Alice", "Bob", "Bob"],
            "score": [10, None, None],
        })

        report = get_report(frame)

        self.assertEqual(report["rows"], 3)
        self.assertEqual(report["columns"], 2)
        self.assertEqual(report["missing_cells"], 2)
        self.assertEqual(report["duplicate_rows"], 1)
        self.assertEqual(report["missing_by_column"]["score"], 2)

    def test_trim_whitespace_and_remove_duplicates(self):
        frame = pd.DataFrame({
            "name": [" Alice ", "Bob", "Bob", "   "],
            "score": [10, None, None, 4],
        })

        result = clean_data(frame)

        self.assertEqual(len(result), 3)
        self.assertEqual(result.loc[0, "name"], "Alice")
        self.assertEqual(result.loc[1, "name"], "Bob")
        self.assertTrue(pd.isna(result.loc[2, "name"]))

    def test_drop_rows_with_missing_values(self):
        frame = pd.DataFrame({
            "name": [" Alice ", "Bob", "   "],
            "score": [10, None, 4],
        })

        result = clean_data(frame, missing="drop")

        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "name"], "Alice")
        self.assertEqual(result.loc[0, "score"], 10)

    def test_fill_missing_values(self):
        frame = pd.DataFrame({
            "name": ["Alice", None],
            "score": [10, None],
        })

        result = clean_data(frame, missing="fill", fill_value="N/A")

        self.assertFalse(result.isna().any().any())
        self.assertEqual(result.loc[1, "name"], "N/A")
        self.assertEqual(result.loc[1, "score"], "N/A")

    def test_duplicate_mode_all_removes_every_copy(self):
        frame = pd.DataFrame({
            "value": [1, 2, 2, 3, 3, 3, 4],
        })

        result = clean_data(frame, duplicates="all")

        self.assertEqual(result["value"].tolist(), [1, 4])

    def test_invalid_missing_mode_raises_error(self):
        frame = pd.DataFrame({"value": [1, 2]})

        with self.assertRaises(DataForgeError):
            clean_data(frame, missing="invalid")

    def test_invalid_duplicate_mode_raises_error(self):
        frame = pd.DataFrame({"value": [1, 2]})

        with self.assertRaises(DataForgeError):
            clean_data(frame, duplicates="invalid")

    def test_missing_input_file_raises_error(self):
        path = self.temp_path / "missing.csv"

        with self.assertRaises(DataForgeError):
            validate_input_path(path)

    def test_empty_input_file_raises_error(self):
        path = self.temp_path / "empty.csv"
        path.write_text("", encoding="utf-8")

        with self.assertRaises(DataForgeError):
            load_data(path)

    def test_csv_load_and_save_round_trip(self):
        source = self.temp_path / "input.csv"
        output = self.temp_path / "cleaned.csv"

        pd.DataFrame({
            "name": ["Alice", "Bob"],
            "score": [10, 20],
        }).to_csv(source, index=False)

        loaded = load_data(source)
        saved_path = save_data(loaded, output, source)
        reloaded = load_data(saved_path)

        self.assertTrue(output.exists())
        pd.testing.assert_frame_equal(loaded, reloaded)
        self.assertTrue(source.exists())

    def test_cannot_overwrite_original_file(self):
        source = self.temp_path / "input.csv"
        source.write_text("name\nAlice\n", encoding="utf-8")

        frame = pd.DataFrame({"name": ["Bob"]})

        with self.assertRaises(DataForgeError):
            save_data(frame, source, source)

        self.assertEqual(
            source.read_text(encoding="utf-8"),
            "name\nAlice\n",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
