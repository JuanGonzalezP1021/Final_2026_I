import tkinter as tk
from tkinter import ttk


class KPICard(ttk.Frame):

    def __init__(self, parent, title, formula, **kw):
        super().__init__(parent, padding=8, **kw)

        self.configure(
            relief='ridge',
            borderwidth=1
        )

        ttk.Label(
            self,
            text=title,
            font=('Segoe UI', 9, 'bold'),
            foreground='#415a77'
        ).pack(anchor='w')

        self.value_var = tk.StringVar(value='--')

        ttk.Label(
            self,
            textvariable=self.value_var,
            font=('Segoe UI', 18, 'bold'),
            foreground='#0d1b2a'
        ).pack(anchor='w')

        ttk.Label(
            self,
            text=formula,
            font=('Segoe UI', 7),
            foreground='#6c757d'
        ).pack(anchor='w')

    def set_value(self, value):
        self.value_var.set(value)