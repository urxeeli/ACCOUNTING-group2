"""Look and feel: ttk styles and the shared table (Treeview) builder."""
from tkinter import ttk

from constants import (
    ACCENT_COLOR,
    FONT,
    PRIMARY_COLOR,
    PRIMARY_LIGHT,
    TAB_BG,
    TREEVIEW_BG,
    TREEVIEW_HEADER,
    TREEVIEW_HEADER_BG,
    TREEVIEW_SELECT,
)


class StyleMixin:
    def set_style(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Root and containers
        s.configure(".", font=FONT, background=TAB_BG)
        s.configure("TFrame", background=TAB_BG)

        # Treeview (clean tables with hover, subtle dividers)
        s.configure("Treeview", rowheight=28,
                    background=TREEVIEW_BG,
                    fieldbackground=TREEVIEW_BG,
                    borderwidth=0,
                    relief="flat")
        s.map("Treeview", background=[("selected", TREEVIEW_SELECT)],
              foreground=[("selected", "white")])

        # Treeview grid lines (subtle separation)
        s.configure("Treeview.Heading", background=TREEVIEW_HEADER_BG,
                    foreground=TREEVIEW_HEADER,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat",
                    padding=(8, 4),
                    borderwidth=0)
        s.map("Treeview.Heading", background=[("active", PRIMARY_COLOR)])

        # Buttons (clean, consistent with subtle hover)
        s.configure("TButton", padding=(10, 6),
                    font=FONT,
                    borderwidth=1,
                    relief="flat")
        s.map("TButton", background=[("active", PRIMARY_LIGHT),
                                     ("pressed", PRIMARY_COLOR)])

        # Primary action button (Accent color - subtle coral)
        s.configure("Accent.TButton", background=ACCENT_COLOR, foreground="white",
                    borderwidth=0,
                    padding=(12, 7))
        s.map("Accent.TButton", background=[("active", "#d35400")],
              foreground=[("disabled", "#eeeeee"), ("!disabled", "white")])

        # Notebook tabs (titled, clean separators)
        s.configure("TNotebook",
                    background=TAB_BG,
                    borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=TAB_BG,
                    font=("Segoe UI", 10, "bold"),
                    padding=(12, 8),
                    compound="left",
                    focuscolor="none")

        # Labels (subtle hierarchy)
        s.configure("TLabel",
                    background=TAB_BG,
                    foreground="#555555",
                    font=("Segoe UI", 9))
        s.configure("TLabel.Title",
                    background=TAB_BG,
                    foreground=PRIMARY_COLOR,
                    font=("Segoe UI", 12, "bold"))

    def make_tree(self, parent, cols, heads, widths, left=(), show="headings", hscroll=False):
        """Create a clean table with hover states and comfortable spacing."""
        box = ttk.Frame(parent, padding=4)
        box.pack(fill="both", expand=True)

        t = ttk.Treeview(box, columns=cols, show=show, selectmode="browse")
        t.configure(style="Treeview")

        # Configure columns
        for c, h, w in zip(cols, heads, widths):
            a = "w" if c in left else "e"
            t.heading(c, text=h, anchor=a)
            t.column(c, width=w, minwidth=w if not hscroll else 80,
                     anchor=a, stretch=c in left)

        # Scrollbars
        ys = ttk.Scrollbar(box, command=t.yview)
        t.configure(yscrollcommand=ys.set)
        if hscroll:
            xs = ttk.Scrollbar(box, orient="horizontal", command=t.xview)
            t.configure(xscrollcommand=xs.set)
            xs.pack(side="bottom", fill="x", pady=(0, 0))
        ys.pack(side="right", fill="y")
        t.pack(side="left", fill="both", expand=True)

        return t
