"""Unit tests for upload parsing and validation. No database required."""
import io
import unittest
from decimal import Decimal

import openpyxl

from app import (
    UploadError,
    detect_delimiter,
    normalize_month,
    parse_amount,
    parse_csv,
    parse_xlsx,
    validate_rows,
)


class NormalizeMonthTests(unittest.TestCase):
    def test_case_and_whitespace_are_normalised(self):
        for raw in ("january", " January ", "JANUARY"):
            self.assertEqual(normalize_month(raw), "January")

    def test_abbreviations_are_accepted(self):
        self.assertEqual(normalize_month("Jan"), "January")
        self.assertEqual(normalize_month("sept"), "September")
        self.assertEqual(normalize_month("Sep"), "September")

    def test_unknown_values_return_none(self):
        for raw in ("Smarch", "", "13", None):
            self.assertIsNone(normalize_month(raw))


class ParseAmountTests(unittest.TestCase):
    def test_zero_is_a_valid_amount(self):
        # Regression: a falsy-check used to silently drop 0 amounts.
        self.assertEqual(parse_amount(0), Decimal("0.00"))
        self.assertEqual(parse_amount("0"), Decimal("0.00"))

    def test_numbers_strings_and_thousand_separators(self):
        self.assertEqual(parse_amount(1234.5), Decimal("1234.50"))
        self.assertEqual(parse_amount("1,234.567"), Decimal("1234.57"))
        self.assertEqual(parse_amount("-150"), Decimal("-150.00"))

    def test_rejects_non_numeric_nan_inf_bool_and_out_of_range(self):
        for bad in ("abc", "nan", "inf", "-Infinity", True, "100000000"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                parse_amount(bad)


class ValidateRowsTests(unittest.TestCase):
    def test_splits_valid_rows_from_problems_with_sheet_row_numbers(self):
        valid, problems = validate_rows([
            ("Jan", 100),
            ("Smarch", 5),
            ("March", None),
            ("April", "oops"),
            ("May", 0),
        ])
        self.assertEqual(valid, [("January", Decimal("100.00")), ("May", Decimal("0.00"))])
        self.assertEqual([p["row"] for p in problems], [3, 4, 5])  # header is row 1


class CsvParsingTests(unittest.TestCase):
    def test_detect_delimiter(self):
        self.assertEqual(detect_delimiter("Month,Amount\n"), ",")
        self.assertEqual(detect_delimiter("Month;Amount\n"), ";")
        self.assertEqual(detect_delimiter("Month\tAmount\n"), "\t")
        self.assertIsNone(detect_delimiter("just free text"))

    def test_bom_and_semicolon_csv(self):
        data = "﻿Month;Amount\nJanuary;10\nFebruary;20\n".encode("utf-8")
        self.assertEqual(parse_csv(data), [("January", "10"), ("February", "20")])

    def test_non_utf8_is_rejected(self):
        with self.assertRaises(UploadError):
            parse_csv(b"\xff\xfe\x00bad")

    def test_single_column_is_rejected_as_unsupported(self):
        with self.assertRaises(UploadError):
            parse_csv(b"Month\nJanuary\n")


class XlsxParsingTests(unittest.TestCase):
    def _workbook_bytes(self, rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Month", "Amount"])
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_reads_rows_and_keeps_zero(self):
        data = self._workbook_bytes([["January", 100], ["February", 0]])
        self.assertEqual(parse_xlsx(data), [("January", 100), ("February", 0)])

    def test_corrupt_zip_raises_upload_error(self):
        with self.assertRaises(UploadError):
            parse_xlsx(b"PK this is not really a workbook")


if __name__ == "__main__":
    unittest.main()
