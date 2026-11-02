"""Tab 4: Trial Balance screen."""
import tkinter as tk
from tkinter import filedialog, ttk
from decimal import Decimal

from constants import ZERO, fmt


class TrialBalanceMixin:
    def build_trial_balance(self, nb):
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  Trial Balance  ")
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 4))
        self.tb_status = tk.StringVar()
        ttk.Label(top, textvariable=self.tb_status, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(top, text="Export CSV", command=self.export_trial_balance_csv).pack(side="right")

        cols = ("acct",) + ("Dr", "Cr")
        self.tt = self.make_tree(tab, cols, ["Account Name", "Debit", "Credit"], [200, 130, 130],
                                 left=("acct",), hscroll=True)
        self.tt.tag_configure("odd", background="#ffffff")
        self.tt.tag_configure("even", background="#f5f8fa")
        self.tt.tag_configure("total", background="#e1e9ef", font=("Segoe UI", 10, "bold"))

    def calculate_trial_balance(self):
        """Return unadjusted account balances, with each balance on its normal side."""
        names = self.all_account_names()
        dr = {n: ZERO for n in names}
        cr = {n: ZERO for n in names}
        for e in self.entries:
            if e.get("adj", False):
                continue
            a = Decimal(e["amount"])
            dr[e["debit"]] += a
            cr[e["credit"]] += a

        rows = []
        for i, n in enumerate(names):
            balance = dr[n] - cr[n]
            rows.append((n, max(balance, ZERO), max(-balance, ZERO), "even" if i % 2 else ""))

        totals = (sum((row[1] for row in rows), ZERO),
                  sum((row[2] for row in rows), ZERO))
        total_row = ("TOTAL", totals[0], totals[1], "total")

        bal_ok = totals[0] == totals[1]
        status = f"Debit balance: {fmt(totals[0])}  |  Credit balance: {fmt(totals[1])}"
        if bal_ok:
            status += "  ✓"
        return rows, total_row, bal_ok, status

    def export_trial_balance_csv(self):
        """Export trial balance to CSV."""
        rows, total_row, _, _ = self.calculate_trial_balance()
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="trial_balance.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        csv_rows = [[name, fmt(dr), fmt(cr)] for name, dr, cr, _ in rows]
        csv_rows.append([total_row[0], fmt(total_row[1]), fmt(total_row[2])])
        self.write_csv_file(path, ["Account Name", "Debit", "Credit"], csv_rows, "Trial Balance")

    def refresh_trial_balance(self):
        rows, total_row, _, status = self.calculate_trial_balance()
        self.tt.delete(*self.tt.get_children())
        for name, dr, cr, tag in rows:
            self.tt.insert("", "end", values=[name, fmt(dr), fmt(cr)], tags=(tag,) if tag else ())
        self.tt.insert("", "end",
                       values=[total_row[0], fmt(total_row[1]), fmt(total_row[2])],
                       tags=("total",))
        self.tb_status.set(status)