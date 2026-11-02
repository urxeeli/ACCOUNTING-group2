"""Saving/loading the data file and the account list."""
import csv
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox

from constants import CHART, DATA_FILE, DATE_PARSE, DATETIME_PARSE, TYPES


class DataMixin:
    def load(self):
        self._data_load_failed = False
        data_path = DATA_FILE
        if not os.path.exists(data_path) and getattr(sys, "frozen", False):
            executable_dir = os.path.dirname(sys.executable)
            parent_dir = os.path.dirname(executable_dir)
            legacy_paths = (
                os.path.join(executable_dir, "accounting_data.json"),
                os.path.join(parent_dir, "accounting_data.json"),
                os.path.join(parent_dir, "fixed", "accounting_data.json"),
            )
            data_path = next((path for path in legacy_paths if os.path.isfile(path)), data_path)
        try:
            with open(data_path, encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError("The data file must contain a JSON object.")
            loaded_entries = []
            for record in d.get("entries", []):
                if not isinstance(record, dict):
                    raise ValueError("An entry in the data file is not an object.")
                entry_date = DATE_PARSE(record.get("date"))
                amount_text = str(record.get("amount", "0"))
                try:
                    amount = Decimal(amount_text)
                except InvalidOperation as err:
                    raise ValueError(f"Invalid transaction amount: {amount_text!r}.") from err
                debit = str(record.get("debit", "")).strip()
                credit = str(record.get("credit", "")).strip()
                if not amount.is_finite() or amount <= 0 or not debit or not credit or debit == credit:
                    raise ValueError("A transaction has an invalid amount or account.")
                loaded_entries.append({
                    "date": entry_date,
                    "datetime": DATETIME_PARSE(record.get("datetime", record.get("date"))),
                    "debit": debit,
                    "credit": credit,
                    "amount": str(amount),
                    "desc": str(record.get("desc", "")),
                    "adj": bool(record.get("adj", False)),
                })
            custom = d.get("custom", {})
            if not isinstance(custom, dict) or any(
                not isinstance(name, str) or account_type not in TYPES
                for name, account_type in custom.items()
            ):
                raise ValueError("Custom accounts in the data file must be an object.")
            self.entries = loaded_entries
            self.custom = custom
        except FileNotFoundError:
            self.entries, self.custom = [], {}
        except (OSError, ValueError, TypeError) as err:
            self.entries, self.custom = [], {}
            recover = messagebox.askyesno(
                "Data file could not be loaded",
                f"The existing data file could not be read:\n{err}\n\n"
                "Would you like to preserve a backup of the damaged file and start with an empty ledger? "
                "The original will not be overwritten.",
            )
            if not recover:
                self._data_load_failed = True
                return

            backup_path = (
                f"{data_path}.corrupt-"
                f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.bak"
            )
            try:
                shutil.copy2(data_path, backup_path)
            except OSError as backup_error:
                self._data_load_failed = True
                messagebox.showerror(
                    "Backup failed",
                    f"The damaged file was not changed, but a backup could not be created:\n"
                    f"{backup_error}\n\nNo new entries can be saved until the file is recovered.",
                )
                return

            self._data_load_failed = False
            messagebox.showinfo(
                "Backup created",
                "The damaged data file was preserved. No complete transactions could be loaded, "
                f"so the app has started with an empty ledger.\n\nBackup: {backup_path}",
            )

    def save(self):
        if getattr(self, "_data_load_failed", False):
            messagebox.showerror(
                "Save blocked",
                "The existing accounting data could not be loaded. Reset all data to replace the damaged file.",
            )
            return False
        directory = os.path.dirname(DATA_FILE)
        temp_path = None
        try:
            os.makedirs(directory, exist_ok=True)
            serialized_entries = []
            for entry in self.entries:
                serialized_entries.append({
                    **entry,
                    "date": entry["date"].isoformat(),
                    "datetime": entry["datetime"].isoformat(),
                })
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", newline="", dir=directory,
                prefix=".accounting_data_", suffix=".tmp", delete=False,
            ) as f:
                temp_path = f.name
                json.dump({"entries": serialized_entries, "custom": self.custom},
                          f, indent=2, ensure_ascii=False)
            os.replace(temp_path, DATA_FILE)
            return True
        except (OSError, TypeError, ValueError) as err:
            messagebox.showwarning("Save failed", str(err))
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as err:
                    messagebox.showwarning("Temporary file cleanup failed", str(err))

    def write_csv_file(self, path, headers, rows, report_name):
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        except OSError as err:
            messagebox.showerror("Export failed", str(err))
            return False
        messagebox.showinfo("Export", f"{report_name} exported to {os.path.basename(path)}")
        return True

    def all_account_names(self):
        """Return all account names in the same order as Journal dropdowns: CHART first, then custom."""
        return [n for n, _ in CHART] + list(self.custom)

    def types(self):
        t = dict(CHART)
        t.update(self.custom)
        return t