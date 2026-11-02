"""Tab 6: Classified Balance Sheet screen."""
from tkinter import filedialog, ttk
from decimal import Decimal

from constants import ASSET, LIAB, CAP, DRAW, REV, EXP, ZERO, fmt
from data import DataMixin


class ClassifiedBalanceSheetMixin(DataMixin):
    def build_classified_balance_sheet(self, nb):
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  Classified BS  ")
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 4))
        self.cbs_status = tk.StringVar()
        ttk.Label(top, textvariable=self.cbs_status, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(top, text="Export CSV", command=self.export_classified_balance_sheet_csv).pack(side="right")

        ttk.Label(tab, foreground="#555", font=("Segoe UI", 9),
                  text="Current Assets |  Fixed Assets |  Total Assets\n"
                       "Current Liabilities |  Long-term Liabilities |  Total Liabilities\n"
                       "Owner\'s Equity").pack(anchor="w", pady=(0, 6))

        cols = ("acct",) + ("Dr", "Cr")
        self.cbs = self.make_tree(tab, cols, ["Account Name", "Debit", "Credit"], [260, 130, 130],
                                 left=("acct",), hscroll=True)
        self.cbs.tag_configure("odd", background="#ffffff")
        self.cbs.tag_configure("even", background="#f5f8fa")
        self.cbs.tag_configure("total", background="#e1e9ef", font=("Segoe UI", 10, "bold"))

    def calculate_classified_bs(self):
        """Compute classified balance sheet (assets/liabilities separated by current/fixed)."""
        types, names = self.types(), self.all_account_names()
        balances = {name: ZERO for name in names}
        for e in self.entries:
            a = Decimal(e["amount"])
            balances[e["debit"]] += a
            balances[e["credit"]] -= a

        rows = []
        totals = {"total_assets": ZERO, "total_liab": ZERO, "equity": ZERO}

        def append_account(name, normal_balance, normal_side, tag=""):
            debit, credit = (normal_balance, ZERO) if normal_balance >= 0 else (ZERO, -normal_balance)
            if normal_side == "credit":
                debit, credit = credit, debit
            rows.append((name, debit, credit, tag))

        def append_group(title, accounts, amount_for_account, normal_side):
            group_total = ZERO
            if accounts:
                rows.append((title, None, None, "total"))
                for name in accounts:
                    amount = amount_for_account(name)
                    group_total += amount
                    append_account(name, amount, normal_side)
                append_account(f"Total {title}", group_total, normal_side, "total")
            return group_total

        fixed_asset_names = {"Accumulated Depreciation Equipment", "Equipment", "Furniture", "Vehicles"}
        current_assets = [n for n in names if types.get(n) == ASSET and n not in fixed_asset_names]
        fixed_assets = [n for n in names if types.get(n) == ASSET and n in fixed_asset_names]
        current_liabilities = [n for n in names if types.get(n) == LIAB and n != "Notes Payable"]
        long_term_liabilities = [n for n in names if types.get(n) == LIAB and n == "Notes Payable"]

        totals["total_assets"] = (
            append_group("Current Assets", current_assets, lambda n: balances[n], "debit")
            + append_group("Fixed Assets", fixed_assets, lambda n: balances[n], "debit")
        )
        totals["total_liab"] = (
            append_group("Current Liabilities", current_liabilities, lambda n: -balances[n], "credit")
            + append_group("Long-term Liabilities", long_term_liabilities, lambda n: -balances[n], "credit")
        )

        capital_accounts = [n for n in names if types.get(n) == CAP]
        drawing_accounts = [n for n in names if types.get(n) == DRAW]
        capital = sum((-balances[n] for n in capital_accounts), ZERO)
        drawings = sum((balances[n] for n in drawing_accounts), ZERO)
        revenue = ZERO
        expenses = ZERO
        for e in self.entries:
            amount = Decimal(e["amount"])
            if types.get(e["debit"]) == REV:
                revenue -= amount
            elif types.get(e["debit"]) == EXP:
                expenses += amount
            if types.get(e["credit"]) == REV:
                revenue += amount
            elif types.get(e["credit"]) == EXP:
                expenses -= amount
        net_income = revenue - expenses
        totals["equity"] = capital - drawings + net_income
        if capital_accounts or drawing_accounts or net_income:
            rows.append(("Owner's Equity", None, None, "total"))
            for name in capital_accounts:
                append_account(name, -balances[name], "credit")
            for name in drawing_accounts:
                append_account(name, balances[name], "debit")
            if net_income:
                append_account("Current Net Income" if net_income > 0 else "Current Net Loss",
                               net_income, "credit")
            append_account("Total Owner's Equity", totals["equity"], "credit", "total")

        status = (f"Assets: {fmt(totals['total_assets'])}  |  "
                  f"Liabilities: {fmt(totals['total_liab'])}  |  "
                  f"Equity: {fmt(totals['equity'])}  |  "
                  f"{'Balanced' if totals['total_assets'] == totals['total_liab'] + totals['equity'] else 'Out of balance'}")
        return rows, totals, status

    def export_classified_balance_sheet_csv(self):
        """Export classified balance sheet to CSV."""
        rows, _, _ = self.calculate_classified_bs()
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="classified_bs.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        csv_rows = [[name, fmt(debit), fmt(credit)] for name, debit, credit, _ in rows]
        self.write_csv_file(path, ["Account Name", "Debit", "Credit"], csv_rows,
                            "Classified Balance Sheet")

    def refresh_classified_balance_sheet(self):
        rows, _, status = self.calculate_classified_bs()
        self.cbs.delete(*self.cbs.get_children())
        for name, dr, cr, tag in rows:
            self.cbs.insert("", "end", values=[name, fmt(dr), fmt(cr)], tags=(tag,) if tag else ())
        self.cbs_status.set(status)