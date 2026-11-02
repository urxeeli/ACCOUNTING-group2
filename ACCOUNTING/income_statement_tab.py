"""Tab 5: Income Statement screen."""
import tkinter as tk
from tkinter import filedialog, ttk
from decimal import Decimal

from constants import REV, EXP, ZERO, fmt


class IncomeStatementMixin:
    def build_income_statement(self, nb):
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  Income Statement  ")
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 4))
        self.is_status = tk.StringVar()
        ttk.Label(top, textvariable=self.is_status, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(top, text="Export CSV", command=self.export_income_statement_csv).pack(side="right")

        cols = ("acct",) + ("Dr", "Cr")
        self.it = self.make_tree(tab, cols, ["Account Name", "Debit", "Credit"], [200, 130, 130],
                                 left=("acct",), hscroll=True)
        self.it.tag_configure("odd", background="#ffffff")
        self.it.tag_configure("even", background="#f5f8fa")
        self.it.tag_configure("rev", background="#d4edda", font=("Segoe UI", 10, "bold"))
        self.it.tag_configure("exp", background="#f8d7da", font=("Segoe UI", 10, "bold"))

    def calculate_income_statement(self):
        """Compute income statement: revenue minus expenses."""
        types, names = self.types(), self.all_account_names()
        revenue = {n: ZERO for n in names if types.get(n) == REV}
        expense = {n: ZERO for n in names if types.get(n) == EXP}
        for e in self.entries:
            a = Decimal(e["amount"])
            if e["debit"] in revenue:
                revenue[e["debit"]] -= a
            elif e["debit"] in expense:
                expense[e["debit"]] += a
            if e["credit"] in revenue:
                revenue[e["credit"]] += a
            elif e["credit"] in expense:
                expense[e["credit"]] -= a

        rows = []
        for n in names:
            if n in revenue and revenue[n]:
                rows.append((n, max(-revenue[n], ZERO), max(revenue[n], ZERO), "rev"))
            elif n in expense and expense[n]:
                rows.append((n, max(expense[n], ZERO), max(-expense[n], ZERO), "exp"))

        total_revenue = sum(revenue.values(), ZERO)
        total_expenses = sum(expense.values(), ZERO)
        net_income = total_revenue - total_expenses
        net_row = ("NET INCOME" if net_income >= 0 else "NET LOSS",
                   max(net_income, ZERO),
                   max(-net_income, ZERO), "total")

        net_label = "Net income" if net_income >= 0 else "Net loss"
        status = (f"Revenue: {fmt(total_revenue)}  |  Expenses: {fmt(total_expenses)}  |  "
                  f"{net_label}: {fmt(abs(net_income))}")
        return rows, net_row, status

    def export_income_statement_csv(self):
        """Export income statement to CSV."""
        rows, net_row, _ = self.calculate_income_statement()
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="income_statement.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        csv_rows = [[name, fmt(dr), fmt(cr)] for name, dr, cr, _ in rows]
        csv_rows.append([net_row[0], fmt(net_row[1]), fmt(net_row[2])])
        self.write_csv_file(path, ["Account Name", "Debit", "Credit"], csv_rows, "Income Statement")

    def refresh_income_statement(self):
        rows, net_row, status = self.calculate_income_statement()
        self.it.delete(*self.it.get_children())
        for name, dr, cr, tag in rows:
            self.it.insert("", "end", values=[name, fmt(dr), fmt(cr)], tags=(tag,) if tag else ())
        self.it.insert("", "end", values=[net_row[0], fmt(net_row[1]), fmt(net_row[2])], tags="total")
        self.is_status.set(status)