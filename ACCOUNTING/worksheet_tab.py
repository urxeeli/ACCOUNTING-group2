"""Tab 3: Worksheet / Balance Sheet screen."""
import tkinter as tk
from decimal import Decimal
from tkinter import filedialog, messagebox, ttk

from constants import HEADS, SECTION, SECTION_COL, ZERO, fmt, DATE_FORMAT_DT
from data import DataMixin


class WorksheetMixin(DataMixin):
    def build_worksheet(self, nb):
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  Balance Sheet  ")
        self.ws_ledger_data = []
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 4))
        self.ws_status = tk.StringVar()
        ttk.Label(top, textvariable=self.ws_status, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(top, text="Export Ledger CSV", command=self.export_ledger_csv).pack(side="right", padx=4)
        ttk.Button(top, text="Export CSV", command=self.export_worksheet_csv).pack(side="right", padx=4)
        ttk.Label(tab, foreground="#555", text="TB = Trial Balance  |  ADJ = Adjustments  |  "
                  "ATB = Adjusted Trial Balance  |  IS = Income Statement  |  "
                  "OE = Owner's Equity  |  BS = Balance Sheet").pack(anchor="w", pady=(0, 6))
        cols = ("acct",) + tuple(f"c{i}" for i in range(12))
        self.wt = self.make_tree(tab, cols, ["Account Name"] + HEADS, [240] + [88] * 12,
                                 left=("acct",), hscroll=True)
        bold = ("Segoe UI", 10, "bold")
        self.wt.tag_configure("odd", background="#ffffff")
        self.wt.tag_configure("even", background="#f5f8fa")
        self.wt.tag_configure("total", background="#e1e9ef", font=bold)
        self.wt.tag_configure("grand", background="#a8c0cd", font=bold)

    def compute_worksheet(self):
        types, names = self.types(), self.all_account_names()
        tb = {n: [ZERO, ZERO] for n in names}
        adj = {n: [ZERO, ZERO] for n in names}
        for e in self.entries:
            a = Decimal(e["amount"])
            t = adj if e["adj"] else tb
            t[e["debit"]][0] += a
            t[e["credit"]][1] += a

        def split(x):  # net balance -> (Dr, Cr)
            return (x, None) if x > 0 else (None, -x) if x < 0 else (None, None)

        rows = []
        for i, n in enumerate(names):
            tnet = tb[n][0] - tb[n][1]
            anet = tnet + adj[n][0] - adj[n][1]
            c = [None] * 12
            c[0], c[1] = split(tnet)
            c[2], c[3] = adj[n][0] or None, adj[n][1] or None
            c[4], c[5] = split(anet)
            k = SECTION_COL[SECTION[types[n]]]
            c[k], c[k + 1] = c[4], c[5]
            rows.append((n, c, "odd" if i % 2 else ""))

        total = [sum((r[1][j] or ZERO for r in rows), ZERO) for j in range(12)]
        rows.append(("TOTAL", total, "total"))

        ni = total[7] - total[6]  # revenue - expenses
        ni_row = [None] * 12
        if ni >= 0:
            ni_row[6] = ni_row[9] = ni
        else:
            ni_row[7] = ni_row[8] = -ni
        rows.append(("NET INCOME" if ni >= 0 else "NET LOSS", ni_row, "total"))

        ec = (total[9] + (ni_row[9] or ZERO)) - (total[8] + (ni_row[8] or ZERO))
        ec_row = [None] * 12
        if ec >= 0:
            ec_row[8] = ec_row[11] = ec
        else:
            ec_row[9] = ec_row[10] = -ec
        rows.append(("ENDING OWNER'S CAPITAL", ec_row, "total"))

        grand = [None] * 6 + [sum((r[j] or ZERO for r in (total, ni_row, ec_row)), ZERO) for j in range(6, 12)]
        rows.append(("GRAND TOTAL", grand, "grand"))
        ok = {"TB": total[0] == total[1], "ADJ": total[2] == total[3], "ATB": total[4] == total[5],
              "IS": grand[6] == grand[7], "OE": grand[8] == grand[9], "BS": grand[10] == grand[11]}
        return rows, ok

    def compute_ledger(self):
        """Return ledger data for CSV export: list of (date, debit, credit, amount, desc, adj) tuples."""
        ledger = []
        for e in self.entries:
            dr = e.get("debit", "")
            cr = e.get("credit", "")
            when = DATE_FORMAT_DT(e["date"])
            ledger.append((when, dr, cr, e["amount"], e.get("desc", ""), e["adj"]))
        return ledger

    def export_ledger_csv(self):
        """Export ledger transactions to CSV (all accounts or filtered by account)."""
        if not self.ws_ledger_data:
            return messagebox.showinfo("Export", "No ledger data to export.")
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="ledger.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        rows = [
            [row[0], row[1], row[2], fmt(Decimal(row[3])), row[4], row[5]]
            for row in self.ws_ledger_data
        ]
        self.write_csv_file(
            path,
            ["Date", "Debit Account", "Credit Account", "Amount", "Description", "Adjusting"],
            rows,
            "Ledger",
        )

    def export_worksheet_csv(self):
        """Export worksheet to CSV."""
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="worksheet.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        rows = [[name] + [fmt(cell) for cell in cells] for name, cells, _ in self.ws_rows]
        self.write_csv_file(path, ["Account Name"] + HEADS, rows, "Worksheet")

    def refresh_worksheet(self):
        rows, ok = self.compute_worksheet()
        self.ws_rows = rows
        self.ws_ledger_data = self.compute_ledger()
        self.wt.delete(*self.wt.get_children())
        for name, cells, tag in rows:
            self.wt.insert("", "end", values=[name] + [fmt(c) for c in cells], tags=(tag,) if tag else ())
        self.ws_status.set("Columns balanced:   " + "   ".join(f"{k} {'✓' if v else '✗'}" for k, v in ok.items()))