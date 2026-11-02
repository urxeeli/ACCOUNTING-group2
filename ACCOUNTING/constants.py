"""Shared constants and small helper functions used by every part of the app."""
import os
import sys
from datetime import date, datetime
from decimal import Decimal

ZERO = Decimal("0")

def get_data_file():
    """Keep packaged-app data in a writable per-user location."""
    if getattr(sys, 'frozen', False):
        user_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(user_data, "AccountingApp", "accounting_data.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounting_data.json")

DATA_FILE = get_data_file()

# Account type decides which statement columns an account lands in.
ASSET, LIAB, CAP, DRAW, REV, EXP = "Asset", "Liability", "Owner's Capital", "Owner's Drawings", "Revenue", "Expense"
TYPES = [ASSET, LIAB, CAP, DRAW, REV, EXP]
SECTION = {ASSET: "BS", LIAB: "BS", CAP: "OE", DRAW: "OE", REV: "IS", EXP: "IS"}
SECTION_COL = {"IS": 6, "OE": 8, "BS": 10}  # index of the Dr column of each statement

CHART = [  # the dropdown list (from the account-name sheet)
    ("Cash", ASSET), ("Accounts Receivable", ASSET), ("Supplies", ASSET),
    ("Prepaid Insurance", ASSET), ("Prepaid Rent", ASSET), ("Equipment", ASSET),
    ("Accumulated Depreciation Equipment", ASSET), ("Furniture", ASSET), ("Vehicles", ASSET),
    ("Accounts Payable", LIAB), ("Unearned Revenue", LIAB), ("Notes Payable", LIAB),
    ("Salaries Payable", LIAB), ("Owner's Capital", CAP), ("Owner's Drawings", DRAW),
    ("Service Revenue", REV), ("Advertising Expense", EXP), ("Utilities Expense", EXP),
    ("Salaries Expense", EXP), ("Maintenance Expense", EXP), ("Professional Fees Expense", EXP),
    ("Repairs Expense", EXP), ("Rent Expense", EXP), ("Interest Expense", EXP),
    ("Insurance Expense", EXP), ("Supplies Expense", EXP), ("Depreciation Expense", EXP),
]
DATE_FORMAT = "%b %d, %Y"  # "Nov 02, 2026"
# ============ COLOR PALETTE ============
PRIMARY_COLOR = "#2c3e50"          # Deep navy - professional, trustworthy
PRIMARY_LIGHT = "#34495e"
ACCENT_COLOR = "#e67e22"           # Muted coral - subtle highlight
BG_COLOR = "#f8f9fa"               # Very light grey - clean background

# Treeview colors
TREEVIEW_BG = "white"
TREEVIEW_SELECT = "#2c3e50"        # Dark selection with readable white text
TREEVIEW_HEADER = "#ffffff"        # High-contrast header text
TREEVIEW_HEADER_BG = "#4a5c6d"     # Subtle header background

# Good to have
TAB_BG = "white"                   # Tab background

def DATE_PARSE(s):
    """Parse a date entered by the user or loaded from the data file."""
    if s is None:
        return date.today()
    if isinstance(s, datetime):
        return s.date()
    if isinstance(s, date):
        return s
    value = str(s).strip()
    for date_format in (None, DATE_FORMAT):
        try:
            return date.fromisoformat(value) if date_format is None else datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date {value!r}. Use {DATE_FORMAT} or YYYY-MM-DD.")

def DATETIME_PARSE(s):
    """Parse an ISO or display-formatted date, optionally including a time."""
    if s is None:
        return datetime.now()
    if isinstance(s, datetime):
        return s
    if isinstance(s, date):
        return datetime.combine(s, datetime.min.time())
    value = str(s).strip()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        for date_format in (DATE_FORMAT,):
            try:
                return datetime.strptime(value, date_format)
            except ValueError:
                continue
    raise ValueError(f"Invalid date or datetime {value!r}.")

def DATE_FORMAT_DT(d):
    """Format datetime to display-ready date string."""
    return d.strftime(DATE_FORMAT)

HEADS = [f"{p} {s}" for p in ("TB", "ADJ", "ATB", "IS", "OE", "BS") for s in ("Dr", "Cr")]
FONT = ("Segoe UI", 10)


def fmt(v):
    """Whole numbers without decimals; blank for zero/None."""
    if v is None or v == 0:
        return ""
    if isinstance(v, datetime):
        return DATE_FORMAT_DT(v)
    amount = v if isinstance(v, Decimal) else Decimal(str(v))
    return f"{amount:,.0f}" if amount == amount.to_integral_value() else f"{amount:,.2f}"


def balfmt(b):
    return "0" if b == 0 else f"{fmt(abs(b))} {'Dr' if b > 0 else 'Cr'}"