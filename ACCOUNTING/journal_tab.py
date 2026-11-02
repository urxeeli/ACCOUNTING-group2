"""Tab 1: Journal Entry screen."""
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from constants import ASSET, TYPES, fmt, DATE_PARSE, DATE_FORMAT_DT, DATETIME_PARSE


class JournalMixin:
    def build_journal(self, nb):
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  Journal Entry  ")
        form = ttk.LabelFrame(tab, text="New transaction", padding=10)
        form.pack(fill="x")

        self.v_date = tk.StringVar(value=DATE_FORMAT_DT(DATE_PARSE(None)))
        self.v_dr, self.v_cr, self.v_amt, self.v_desc = (tk.StringVar() for _ in range(4))
        self.v_adj = tk.BooleanVar()
        self.e_date = ttk.Entry(form, textvariable=self.v_date, width=13)
        self.cb_dr = ttk.Combobox(form, textvariable=self.v_dr, width=30)
        self.cb_cr = ttk.Combobox(form, textvariable=self.v_cr, width=30)
        self.e_amt = ttk.Entry(form, textvariable=self.v_amt, width=14, justify="right")
        self.e_desc = ttk.Entry(form, textvariable=self.v_desc, width=36)
        fields = [("Date", self.e_date), ("Debit account", self.cb_dr), ("Credit account", self.cb_cr),
                  ("Amount", self.e_amt), ("Description", self.e_desc)]
        for c, (label, w) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=c, sticky="w", padx=4)
            w.grid(row=1, column=c, sticky="ew", padx=4, pady=(2, 6))
            w.bind("<Return>", lambda _: self.add_entry())
        for cb in (self.cb_dr, self.cb_cr):
            cb.bind("<KeyRelease>", self.filter_accounts)
        for c in (1, 2):
            form.columnconfigure(c, weight=1)
        form.columnconfigure(4, weight=2)

        bar = ttk.Frame(form)
        bar.grid(row=2, column=0, columnspan=5, sticky="ew")
        ttk.Checkbutton(bar, text="Adjusting entry (goes to the Adjustments columns)",
                        variable=self.v_adj).pack(side="left", padx=4)
        ttk.Button(bar, text="Add Entry", style="Accent.TButton", command=self.add_entry).pack(side="right", padx=4)

        self.status = tk.StringVar(value="Pick or type the accounts, enter the amount, then press Enter.")
        ttk.Label(tab, textvariable=self.status, foreground="#555").pack(anchor="w", pady=(6, 4))

        self.jt = self.make_tree(tab, ("date", "part", "dr", "cr"), ("Date", "Particulars", "Dr", "Cr"),
                                 (150, 520, 130, 130), left=("date", "part"))
        self.jt.tag_configure("adj", background="#fff3cd", font=("Segoe UI", 10, "bold"))
        self.jt.tag_configure("desc", foreground="#666", font=("Segoe UI", 9, "italic"))
        self.jt.tag_configure("rev", background="#e0f7fa", foreground="#006064")
        self.jt.tag_configure("exp", background="#fdf0f0", foreground="#c62828")
        self.jt.tag_configure("asset", background="#e8f4f8", foreground="#0277bd")
        self.jt.tag_configure("badge", foreground="#333", font=("Segoe UI", 8, "bold"))

        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Delete Selected Entry", command=self.delete_journal_entry).pack(side="left")
        ttk.Button(btns, text="Reset All", command=self.reset_all).pack(side="left", padx=8)

    def get_account_type(self, account_name):
        """Return account type for visual styling."""
        return self.types().get(account_name, "OTHER")

    def filter_accounts(self, ev):
        if ev.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape", "Shift_L", "Shift_R"):
            return
        t = ev.widget.get().strip().lower()
        names = self.all_account_names()
        ev.widget["values"] = [n for n in names if t in n.lower()]

    def ask_type(self, name):
        dlg = tk.Toplevel(self.root)
        dlg.title("New account")
        dlg.transient(self.root)
        dlg.resizable(False, False)
        dlg.geometry(f"+{self.root.winfo_rootx() + 420}+{self.root.winfo_rooty() + 260}")
        ttk.Label(dlg, text=f'"{name}" is not in the list.\nWhat type of account is it?',
                  padding=14, justify="center").pack()
        var = tk.StringVar(value=ASSET)
        cb = ttk.Combobox(dlg, textvariable=var, values=TYPES, state="readonly", width=24)
        cb.pack(padx=14)
        res = {"v": None}

        def ok(_=None):
            res["v"] = var.get()
            dlg.destroy()

        ttk.Button(dlg, text="OK", style="Accent.TButton", command=ok).pack(pady=14)
        dlg.bind("<Return>", lambda _: ok())
        dlg.bind("<Escape>", lambda _: dlg.destroy())
        cb.focus_set()
        dlg.wait_visibility()
        dlg.grab_set()
        dlg.wait_window()
        return res["v"]

    def resolve(self, raw):
        """Match typed text to a known account (any case) or ask for the type of a new one."""
        for n in self.all_account_names():
            if n.lower() == raw.lower():
                return n
        t = self.ask_type(raw)
        if t is None:
            return None
        self.custom[raw] = t
        return raw

    def add_entry(self):
        d = self.v_date.get().strip()
        dr_raw = " ".join(self.v_dr.get().split())
        cr_raw = " ".join(self.v_cr.get().split())
        try:
            txt = self.v_amt.get().replace(",", "").replace("₱", "").replace("$", "").strip()
            amt = Decimal(txt)
            if not amt.is_finite() or amt <= 0:
                raise InvalidOperation
            amt = amt.quantize(Decimal("0.01"))
        except InvalidOperation:
            return messagebox.showerror("Amount", "Enter a valid amount greater than 0.")
        if not (d and dr_raw and cr_raw):
            return messagebox.showerror("Missing info", "Date, debit account and credit account are required.")
        if dr_raw.lower() == cr_raw.lower():
            return messagebox.showerror("Same account", "Debit and credit accounts must be different.")
        try:
            entry_date = DATE_PARSE(d)
            entry_datetime = DATETIME_PARSE(d)
        except ValueError as err:
            return messagebox.showerror("Date", str(err))
        custom_before = self.custom.copy()
        dr = self.resolve(dr_raw)
        if not dr:
            return
        cr = self.resolve(cr_raw)
        if not cr:
            self.custom = custom_before
            return
        self.entries.append({
            "date": entry_date,
            "debit": dr,
            "credit": cr,
            "amount": str(amt),
            "desc": self.v_desc.get().strip(),
            "adj": self.v_adj.get(),
            "datetime": entry_datetime
        })
        if not self.save():
            self.entries.pop()
            self.custom = custom_before
            return
        self.refresh()
        for v in (self.v_dr, self.v_cr, self.v_amt, self.v_desc):
            v.set("")
        self.status.set(f"Added: Dr {dr}  /  Cr {cr}  -  {fmt(amt)}")
        self.cb_dr.focus_set()

    def delete_journal_entry(self):
        sel = self.jt.selection()
        if not sel:
            return messagebox.showinfo("Delete", "Click an entry in the journal first.")
        entry = self._journal_entry_by_row.get(sel[0])
        if entry is None:
            return messagebox.showinfo("Delete", "Select a transaction row, not a table heading.")
        if messagebox.askyesno("Delete entry", "Delete this entry?"):
            index = next(i for i, candidate in enumerate(self.entries) if candidate is entry)
            del self.entries[index]
            if not self.save():
                self.entries.insert(index, entry)
                return
            self.refresh()

    def reset_all(self):
        if messagebox.askyesno("Reset all", "Delete ALL entries and custom accounts? This cannot be undone."):
            old_entries, old_custom = self.entries, self.custom
            old_load_failed = getattr(self, "_data_load_failed", False)
            self.entries, self.custom = [], {}
            self._data_load_failed = False
            if not self.save():
                self.entries, self.custom = old_entries, old_custom
                self._data_load_failed = old_load_failed
                return
            self.refresh()

    def refresh_journal(self):
        self.jt.delete(*self.jt.get_children())
        self._journal_entry_by_row = {}
        sorted_entries = sorted(enumerate(self.entries),
                                key=lambda item: item[1].get("datetime", item[1].get("date", "")),
                                reverse=True)
        for index, e in sorted_entries:
            a = Decimal(e["amount"])
            tag = ("adj",) if e["adj"] else ()
            when = DATE_FORMAT_DT(e["date"]) + ("  (adj)" if e["adj"] else "")
            dr_type = self.get_account_type(e["debit"])
            cr_type = self.get_account_type(e["credit"])
            dr_tag = tag + (("asset",) if dr_type == "Asset" else ())
            cr_tag = tag + (("rev",) if cr_type == "Revenue" else
                            ("exp",) if cr_type == "Expense" else
                            ("asset",) if cr_type == "Asset" else ())
            debit_iid, credit_iid = f"entry_{index}_dr", f"entry_{index}_cr"
            self.jt.insert("", "end", iid=debit_iid, values=(when, e["debit"], fmt(a), ""), tags=dr_tag)
            self.jt.insert("", "end", iid=credit_iid,
                           values=("", "      " + e["credit"], "", fmt(a)), tags=cr_tag)
            self._journal_entry_by_row[debit_iid] = e
            self._journal_entry_by_row[credit_iid] = e
            if e["desc"]:
                desc_iid = f"entry_{index}_desc"
                self.jt.insert("", "end", iid=desc_iid, values=("", f"      ({e['desc']})", "", ""),
                               tags=tag + ("desc",))
                self._journal_entry_by_row[desc_iid] = e
        kids = self.jt.get_children()
        if kids:
            self.jt.see(kids[0])