import tempfile
import unittest
import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from constants import CHART, DATE_PARSE, DATETIME_PARSE, ZERO
from data import DataMixin
from income_statement_tab import IncomeStatementMixin
from classified_balance_sheet_tab import ClassifiedBalanceSheetMixin
from trial_balance_tab import TrialBalanceMixin
from worksheet_tab import WorksheetMixin


class AccountingHarness:
    def __init__(self):
        self.entries = [
            self.entry("Cash", "Owner's Capital", "100", False),
            self.entry("Utilities Expense", "Cash", "25", False),
            self.entry("Cash", "Service Revenue", "60", False),
            self.entry("Cash", "Utilities Expense", "5", False),
            self.entry("Depreciation Expense", "Accumulated Depreciation Equipment", "10", True),
        ]
        self.custom = {}

    @staticmethod
    def entry(debit, credit, amount, adjusting):
        entry_date = date(2026, 11, 3)
        return {
            "date": entry_date,
            "datetime": datetime(2026, 11, 3),
            "debit": debit,
            "credit": credit,
            "amount": amount,
            "desc": "",
            "adj": adjusting,
        }

    def all_account_names(self):
        return [name for name, _ in CHART] + list(self.custom)

    def types(self):
        return dict(CHART, **self.custom)


class AccountingCalculationTests(unittest.TestCase):
    def setUp(self):
        self.app = AccountingHarness()

    def test_trial_balance_uses_net_unadjusted_balances(self):
        rows, total, balanced, _ = TrialBalanceMixin.calculate_trial_balance(self.app)
        balances = {name: (debit, credit) for name, debit, credit, _ in rows}

        self.assertEqual(balances["Cash"], (Decimal("140"), ZERO))
        self.assertEqual(balances["Utilities Expense"], (Decimal("20"), ZERO))
        self.assertEqual(balances["Owner's Capital"], (ZERO, Decimal("100")))
        self.assertEqual(balances["Service Revenue"], (ZERO, Decimal("60")))
        self.assertEqual(balances["Depreciation Expense"], (ZERO, ZERO))
        self.assertEqual(total[1:3], (Decimal("160"), Decimal("160")))
        self.assertTrue(balanced)

    def test_income_statement_uses_correct_normal_balances_and_net_income(self):
        rows, net_row, _ = IncomeStatementMixin.calculate_income_statement(self.app)
        by_name = {name: (debit, credit) for name, debit, credit, _ in rows}

        self.assertEqual(by_name["Service Revenue"], (ZERO, Decimal("60")))
        self.assertEqual(by_name["Utilities Expense"], (Decimal("20"), ZERO))
        self.assertEqual(by_name["Depreciation Expense"], (Decimal("10"), ZERO))
        self.assertEqual(net_row[:3], ("NET INCOME", Decimal("30"), ZERO))

    def test_income_statement_reverses_abnormal_account_balances(self):
        self.app.entries = [
            AccountingHarness.entry("Cash", "Service Revenue", "20", False),
            AccountingHarness.entry("Service Revenue", "Cash", "5", False),
            AccountingHarness.entry("Utilities Expense", "Cash", "10", False),
            AccountingHarness.entry("Cash", "Utilities Expense", "30", False),
        ]
        rows, net_row, _ = IncomeStatementMixin.calculate_income_statement(self.app)
        by_name = {name: (debit, credit) for name, debit, credit, _ in rows}

        self.assertEqual(by_name["Service Revenue"], (ZERO, Decimal("15")))
        self.assertEqual(by_name["Utilities Expense"], (ZERO, Decimal("20")))
        self.assertEqual(net_row[:3], ("NET INCOME", Decimal("35"), ZERO))

    def test_classified_balance_sheet_includes_contra_assets_and_current_income(self):
        _, totals, status = ClassifiedBalanceSheetMixin.calculate_classified_bs(self.app)

        self.assertEqual(totals, {
            "total_assets": Decimal("130"),
            "total_liab": ZERO,
            "equity": Decimal("130"),
        })
        self.assertIn("Balanced", status)

    def test_twelve_column_worksheet_balances_each_section(self):
        _, balanced = WorksheetMixin.compute_worksheet(self.app)

        self.assertTrue(all(balanced.values()), balanced)

    def test_date_parsers_accept_supported_formats_and_reject_invalid_dates(self):
        self.assertEqual(DATE_PARSE("2026-11-03"), date(2026, 11, 3))
        self.assertEqual(DATE_PARSE("Nov 03, 2026"), date(2026, 11, 3))
        self.assertEqual(DATETIME_PARSE("2026-11-03T14:30:00"),
                         datetime(2026, 11, 3, 14, 30))
        with self.assertRaises(ValueError):
            DATE_PARSE("2026-02-30")


class DataPersistenceTests(unittest.TestCase):
    def test_save_and_load_serializes_date_objects(self):
        app = DataMixin()
        app.entries = [AccountingHarness.entry("Cash", "Owner's Capital", "100", False)]
        app.custom = {"Consulting Revenue": "Revenue"}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = str(Path(temp_dir) / "accounting_data.json")
            with patch("data.DATA_FILE", data_file):
                self.assertTrue(app.save())
                loaded = DataMixin()
                loaded.load()

            self.assertEqual(loaded.entries, app.entries)
            self.assertEqual(loaded.custom, app.custom)

    def test_csv_export_writes_a_header_and_rows(self):
        app = DataMixin()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.csv"
            with patch("data.messagebox.showinfo"):
                self.assertTrue(app.write_csv_file(
                    str(output_path), ["Account", "Balance"], [["Cash", "100"]], "Report"
                ))
            with output_path.open(encoding="utf-8-sig", newline="") as f:
                self.assertEqual(list(csv.reader(f)), [["Account", "Balance"], ["Cash", "100"]])

    def test_confirmed_corrupt_file_recovery_preserves_original_backup(self):
        app = DataMixin()
        original = '{\n  "entries": [\n    {\n      "date": '

        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "accounting_data.json"
            data_file.write_text(original, encoding="utf-8")
            with (
                patch("data.DATA_FILE", str(data_file)),
                patch("data.messagebox.askyesno", return_value=True),
                patch("data.messagebox.showinfo"),
            ):
                app.load()

            backups = list(Path(temp_dir).glob("accounting_data.json.corrupt-*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)
            self.assertEqual(app.entries, [])
            self.assertFalse(app._data_load_failed)

            with patch("data.DATA_FILE", str(data_file)):
                self.assertTrue(app.save())
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)

    def test_declining_corrupt_file_recovery_prevents_overwrite(self):
        app = DataMixin()
        original = '{"entries":'

        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "accounting_data.json"
            data_file.write_text(original, encoding="utf-8")
            with (
                patch("data.DATA_FILE", str(data_file)),
                patch("data.messagebox.askyesno", return_value=False),
            ):
                app.load()

            self.assertTrue(app._data_load_failed)
            self.assertEqual(data_file.read_text(encoding="utf-8"), original)
            with (
                patch("data.DATA_FILE", str(data_file)),
                patch("data.messagebox.showerror") as showerror,
            ):
                self.assertFalse(app.save())
            self.assertTrue(showerror.called)
            self.assertEqual(data_file.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
