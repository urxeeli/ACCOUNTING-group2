"""Tab 2: Ledger screen."""
import tkinter as tk
from decimal import Decimal
from tkinter import ttk, messagebox

from constants import ZERO, balfmt, fmt, DATE_FORMAT_DT


class LedgerMixin:
    def build_ledger(self, nb):
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  Ledger  ")

        # Top bar with account dropdown
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Account:").pack(side="left", padx=(0, 8))

        self.v_ledger_acct = tk.StringVar(value="All Accounts")
        self.cb_ledger_acct = ttk.Combobox(
            top, textvariable=self.v_ledger_acct, state="readonly", width=40
        )
        self.cb_ledger_acct.pack(side="left")
        self.cb_ledger_acct.bind("<<ComboboxSelected>>", self.on_ledger_account_change)

        # Ledger tree
        self.lt = self.make_tree(tab, ("date", "part", "dr", "cr", "bal"),
                                 ("Date", "Particulars", "Dr", "Cr", "Balance"),
                                 (130, 420, 120, 120, 160), left=("date", "part"))
        self.lt.tag_configure("adj", background="#fff3cd", font=("Segoe UI", 10, "bold"))
        self.lt.tag_configure("total", background="#e1e9ef", font=("Segoe UI", 10, "bold"))

        # Buttons
        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=(8, 4))
        ttk.Button(btns, text="Delete Entry", command=self.delete_ledger_entry).pack(side="right", padx=4)

    def on_ledger_account_change(self, _=None):
        self.refresh_ledger()

    def _post_one_entry(self, e, account):
        """
        Helper to post one entry to totals.
        Returns (dr, cr, parts, date_str) tuple.
        """
        a = Decimal(e["amount"])
        if account == e["debit"]:
            dr, cr, other = a, ZERO, e["credit"]
            when = e["date"]
        elif account == e["credit"]:
            dr, cr, other = ZERO, a, e["debit"]
            when = e["date"]
        else:
            return ZERO, ZERO, None, None
        part = (e.get("desc") or other) + ("  [Adj]" if e["adj"] else "")
        return dr, cr, part, DATE_FORMAT_DT(when)

    def refresh_ledger(self):
        self.lt.delete(*self.lt.get_children())
        self._ledger_entry_by_row = {}

        selected = self.v_ledger_acct.get()
        accounts = self.all_account_names()
        indexed_entries = sorted(
            enumerate(self.entries),
            key=lambda item: item[1].get("datetime", item[1].get("date", "")),
        )

        if selected == "All Accounts":
            for account_index, n in enumerate(accounts):
                lines, bal, sd, sc = [], ZERO, ZERO, ZERO
                for entry_index, e in indexed_entries:
                    dr, cr, part, vs = self._post_one_entry(e, n)
                    if vs is None:
                        continue
                    bal += dr - cr
                    sd += dr
                    sc += cr
                    lines.append((entry_index, e, (vs, part, fmt(dr), fmt(cr), balfmt(bal))))
                if not lines:
                    continue
                parent = self.lt.insert(
                    "", "end", iid=f"account_{account_index}", open=True, tags=("total",),
                    values=("", f"{n} account totals", fmt(sd), fmt(sc), balfmt(bal)),
                )
                for entry_index, e, values in lines:
                    iid = f"entry_{account_index}_{entry_index}"
                    tags = ("adj",) if e["adj"] else ()
                    self.lt.insert(parent, "end", iid=iid, values=values, tags=tags)
                    self._ledger_entry_by_row[iid] = e
        else:
            lines, bal, sd, sc = [], ZERO, ZERO, ZERO
            for entry_index, e in indexed_entries:
                dr, cr, part, vs = self._post_one_entry(e, selected)
                if vs is None:
                    continue
                bal += dr - cr
                sd += dr
                sc += cr
                lines.append((entry_index, e, (vs, part, fmt(dr), fmt(cr), balfmt(bal))))

            if not lines:
                self.lt.insert("", "end", values=("", f"No transactions for {selected} yet.", "", "", ""),
                               tags=("empty",))
                self.lt.tag_configure("empty", foreground="#999", font=("Segoe UI", 10, "italic"))
            else:
                for entry_index, e, values in lines:
                    iid = f"entry_{entry_index}"
                    tags = ("adj",) if e["adj"] else ()
                    self.lt.insert("", "end", iid=iid, values=values, tags=tags)
                    self._ledger_entry_by_row[iid] = e
                self.lt.insert("", "end", values=("", "DEBIT TOTALS", fmt(sd), "", balfmt(sd)),
                               tags=("total",))
                self.lt.insert("", "end", values=("", "CREDIT TOTALS", "", fmt(sc), balfmt(sc)),
                               tags=("total",))

    def delete_ledger_entry(self):
        sel = self.lt.selection()
        if not sel:
            return messagebox.showinfo("Delete", "Click an entry in the ledger first.")
        iid = sel[0]
        entry = self._ledger_entry_by_row.get(iid)
        if entry is None:
            return messagebox.showinfo("Delete", "Select a transaction row, not an account total.")
        if messagebox.askyesno("Delete entry", "Delete this entry?"):
            index = next(i for i, candidate in enumerate(self.entries) if candidate is entry)
            del self.entries[index]
            if not self.save():
                self.entries.insert(index, entry)
                return
            self.refresh()